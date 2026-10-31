import logging
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import END, StateGraph, MessagesState
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.base import BaseStore
from typing_extensions import List

from db.postgres import get_postgres_connection
from db.chroma import get_chroma_db
from api.user_and_answer.user_and_answer_repository import create_user_question_and_answer
from rag_graph.models import llm
from rag_graph.context_evaluators import grade_documents_llm, grade_documents_jev, filter_graded_documents
from typesafe_sdk import TypeSafeError

CONTEXT_EVALUATOR_LLM = "llm"
CONTEXT_EVALUATOR_JEV = "jev"

logger = logging.getLogger(__name__)
vector_store = get_chroma_db()

"""
StateGraph (RagState): StateMachine that represents the workflow
Nodes: Represents llm or functions at the workflow. Typically regular python functions
    Each node receives the current state and can return an updated state
Edges: Specify how the agent transit between nodes
"""

class RagState(MessagesState):
    """
    The state of our application controls what data is input to the application, transferred between steps, and output by the application.
    It is typically a TypedDict, but can also be a Pydantic BaseModel.
    """

    sources: List[str]
    documents: List[Document]
    has_relevant_documents: bool
    hallucination_grade: dict
    answer_grade: float

def __router_choice__(state: RagState):
    """
    Step to decide whether to use the vector store or the LLM based on the user question.
    """
    prompt = [
        ("system", "You are an expert at routing user questions to a vector store or generating answers using only the LLM "),
        ("system", "Use the vector store for questions related to computer scicente, programming, and technology."),
        ("system", "Don't be strigent with keywords in the question related to the topics"),
        ("system", "Otherwise, generate an answer using the LLM."),
        ("system", "Give a binary choice 'vectorstore' or 'llm' based on the question"),
        ("system", "Return a JSON with a single key 'choice' with no premable or explaination"),
        ("human", "{question}"),
    ]

    router = ChatPromptTemplate.from_messages(prompt) | llm | JsonOutputParser()
    question = state["messages"][-1].content
    choice = router.invoke({"question": question})['choice'].lower()

    print (f"🤖 LLM irá te responder...") if choice == 'llm' else print (f"🤖 Vamos buscar contexto...")

    return router.invoke({"question": question})['choice']

def __retrieve_context__(state: RagState):
    """
    Step to retrieve the context from the vector database based on the user question.
    """

    retriever = vector_store.as_retriever()

    print(f"🤖 Recuperando contexto baseado nos documentos para uma melhor resposta...")
    question = state["messages"][-1].content
    documents = retriever.invoke(question)
    print(f"🤖 Contexto recuperado com sucesso...")

    return {"documents": documents, "sources": [doc.id for doc in documents]}

def __retrieved_context_evaluator_llm__(state: RagState):
    """
    Step that evaluates the quality of the retrieved context using the local LLM.
    Context Retrived Judge
    """

    print (f"🤖 Avaliando a qualidade do contexto recuperado...")

    question = state["messages"][-1].content
    grades = grade_documents_llm(question, state["documents"])

    return filter_graded_documents(state["documents"], grades)

def __retrieved_context_evaluator_jev__(state: RagState):
    """
    Step that evaluates the quality of the retrieved context using JEV (TypeSafe).
    Falls back to the local LLM if the TypeSafe API fails.
    """

    print (f"🤖 Avaliando a qualidade do contexto recuperado com o JEV...")

    question = state["messages"][-1].content
    try:
        grades = grade_documents_jev(question, state["documents"])
    except TypeSafeError as e:
        logger.error(f"Falha ao avaliar o contexto com o JEV, utilizando o LLM: {e}")
        return __retrieved_context_evaluator_llm__(state)

    return filter_graded_documents(state["documents"], grades)

CONTEXT_EVALUATORS = {
    CONTEXT_EVALUATOR_LLM: __retrieved_context_evaluator_llm__,
    CONTEXT_EVALUATOR_JEV: __retrieved_context_evaluator_jev__,
}

def __generate_answer__(state: RagState):
    """
    Step that generates the final answer using the LLM based on the retrieved context.
    """

    if state["has_relevant_documents"] == False:
        return {"messages": ["Desculpe, mas não tenho informações suficientes para responder a sua pergunta no momento."], "sources": []}

    print(f"🤖 Gerando a sua resposta...")

    prompt_text = """
    You are an assistant for question-answering tasks related to computer science.
    You should only answer questions related to computer science.
    If the question is not related to computer science, just say you don't know.
    Use only the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know. Use a maximum of ten sentences and keep the answer concise.
    Context: {context}
    Think this step by step and provide a concise answer.
    """

    prompt = ChatPromptTemplate.from_messages([("system", prompt_text)])

    message_tools = [] 
    if "documents" in state:
        for message in state["documents"]:
            message_tools.append(message.page_content)

    sources = state["sources"] if "sources" in state else []
    message_tools = message_tools[::-1]
    retrieved_content = "\n\n".join(doc for doc in message_tools)
    prompt_messages = prompt.invoke({"context": retrieved_content})

    conversation = [
        message
        for message in state["messages"]
        if message.type in ("human", "system")
        or (message.type == "ai" and not message.tool_calls)
    ]

    prompt = prompt_messages.to_messages() + conversation

    response = llm.invoke(prompt)

    return {"messages": [response], "sources": sources}

def __evaluate_answer_backed_by_context__(state: RagState):
    """
    Evaluate if the answer provided by the rag system is in accordance with the context provided.
    """

    print (f"🤖 Avaliando concordância da resposta com o contexto gerado...")

    prompt_template = """
    You are a grader assessing wheather an answer is grounded in or supported by a set of documents. Give an grade score as an float on a scale of 0 to 10
    , where 0 is when the set of documents are completely irrelevant to the answer and 10 is when the set of documents fully supports the answer. Provide
    the response as an JSON, with no preamble or explanation with two keys: score, and reasoning. The reasoning key should contain the explanation on why
    that score was provided.

    Set of documents: {documents} 
    Here is the answer: {answer}
    """
    prompt = ChatPromptTemplate.from_template(prompt_template)
    hallucination_grader = prompt | llm | JsonOutputParser()
    answer = state["messages"][-1]
    documents = state["documents"]

    result = hallucination_grader.invoke({"documents": documents, "answer": answer})

    return {"hallucination_grade": result}

def __save_question_and_answer__(state: RagState, config):
    """
    Save question and answer pair from the system at the postgres database, so it can be judge in another process
    """

    print (f"🤖 Gerando registro de pergunta e resposta no banco de dados")

    question = state["messages"][-2].content
    answer = state["messages"][-1].content
    conn = get_postgres_connection()
    user_id = config["metadata"]["user_id"]

    create_user_question_and_answer(conn, user_id, question, answer)

def create_graph(checkpointer: BaseCheckpointSaver, store: BaseStore = None, context_evaluator: str = None):
    """
    context_evaluator: "llm" or "jev". Defaults to the CONTEXT_EVALUATOR env var, or "llm" when unset.
    """

    context_evaluator = (context_evaluator or os.getenv("CONTEXT_EVALUATOR") or CONTEXT_EVALUATOR_LLM).lower()
    if context_evaluator not in CONTEXT_EVALUATORS:
        raise ValueError(f"Avaliador de contexto inválido: '{context_evaluator}'. Opções: {', '.join(CONTEXT_EVALUATORS)}")

    graph_builder = StateGraph(RagState)
    graph_builder.add_node("retrieve_context", __retrieve_context__)
    graph_builder.add_node("retrieved_context_evaluator", CONTEXT_EVALUATORS[context_evaluator])
    graph_builder.add_node("generate_answer", __generate_answer__)
    graph_builder.add_node("save_question_and_answer", __save_question_and_answer__)

    graph_builder.set_conditional_entry_point(__router_choice__, {"vectorstore": "retrieve_context", "llm": "generate_answer"})
    graph_builder.add_edge("retrieve_context", "retrieved_context_evaluator")
    graph_builder.add_edge("retrieved_context_evaluator", "generate_answer")
    graph_builder.add_edge("generate_answer", "save_question_and_answer")
    graph_builder.add_edge("save_question_and_answer", END)

    graph = graph_builder.compile(checkpointer=checkpointer, store=store)

    return graph
