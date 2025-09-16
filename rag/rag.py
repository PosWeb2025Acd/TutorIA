import os

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph, MessagesState
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.base import BaseStore
from typing_extensions import List
from tavily import TavilyClient

from db.postgres import get_postgres_connection
from db.chroma import get_chroma_db
from api.user_and_answer.user_and_answer_repository import create_user_question_and_answer

MODEL = "llama3.1:8b"
EVALUATION_RELEVANT = "relevant"
EVALUATION_PARTIALLY_RELEVANT = "partially_relevant"
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL")

llm = ChatOllama(model=MODEL, verbose=False, temperature=0.0, base_url=OLLAMA_BASE_URL)
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
    web_search_recomended: bool
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

def __retrieved_context_evaluator__(state: RagState):
    """
    Step that evaluates the quality of the retrieved context.
    Context Retrived Judge
    """

    print (f"🤖 Avaliando a qualidade do contexto recuperado...")

    prompt_data = """
    You are a grader assessing relevance of a retrieved document to a user question.
    Given a user question and retrieved document, determine if the document provider has sufficient context to answer the question accurately.
    To evaluate if the document is relevant, you can check if the document contains keywords related to the user question.
    It does not need to be a stringent test. The goal is to filter out erroneous retrievals
    Give a score 'relevant', 'partially_relevant' or 'not_relevant' to indicate wheter the document is relevant to the question
    Provide the score as a JSON with a single key 'evaluation' and no premable or explaination
    Document to be used for evaluation: {documents}
    Here is the user question: {question}
    """

    prompt = PromptTemplate.from_template(prompt_data)
    retrieval_grader = prompt | llm | JsonOutputParser()
    question = state["messages"][-1].content

    relevant_documents = []
    partially_relevant_documents = []

    for doc in state["documents"]:
        result = retrieval_grader.invoke({
            "question": question,
            "documents": doc.page_content,
        })

        evaluation = result['evaluation'].lower()

        if evaluation == EVALUATION_RELEVANT:
            relevant_documents.append(doc)
        if evaluation == EVALUATION_PARTIALLY_RELEVANT:
            partially_relevant_documents.append(doc)

    filtered_documents = relevant_documents + partially_relevant_documents

    web_search_recommended = False if len(relevant_documents) > 0 else True

    return {"documents": filtered_documents, "sources": [doc.id for doc in filtered_documents], "web_search_recomended": web_search_recommended}

def __decision_based_on_evaluation__(state: RagState):
    """
    Step to decide whether to generate an answer based on the retrieved context or to perform a web search.
    """

    web_search_recommended = state["web_search_recomended"]
    if web_search_recommended:
        print("🤖 A avaliação do contexto recuperado indicou que uma busca na web pode ser útil para complementar a resposta.")
        return "web_search"

    print("🤖 A avaliação do contexto recuperado indicou que é possível gerar uma resposta com o contexto disponível.")
    return "generate_answer"

def __web_search__(state: RagState):
    """
    Step that permorms a web search using the Tavily API to complement the answer or to gather the necessary context.
    """

    print (f"🤖 Realizando uma busca na web para complementar a resposta...")

    tavily_token = os.getenv("TAVILY_TOKEN")
    tavily_client = TavilyClient(api_key=tavily_token)
    question = state["messages"][-1].content
    response = tavily_client.search(question, max_results=5)

    results = response["results"] if "results" in response else []
    web_documents = []
    sources = []

    for web_result in results:
        web_documents.append(Document(page_content=web_result["content"], metadata={"source": web_result["url"], "title": web_result["title"]}))
        sources.append(web_result["url"])

    print (f"🤖 Busca na web finalizada...")

    return {"documents": state["documents"] + web_documents, "sources": state["sources"] + sources}

def __generate_answer__(state: RagState):
    """
    Step that generates the final answer using the LLM based on the retrieved context.
    """

    print(f"🤖 Gerando a sua resposta...")

    prompt_text = """
    You are an assistant for question-answering tasks related to computer science.
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
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

def __evaluate_answer__(state: RagState):
    """
    Evaluate the answer provided by the rag system using a different LLM.
    LLM as a judge final step
    """

    print (f"🤖 Avaliando a resposta gerada pelo RAG...")

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

def create_graph(checkpointer: BaseCheckpointSaver, store: BaseStore = None):
    graph_builder = StateGraph(RagState)
    graph_builder.add_node("retrieve_context", __retrieve_context__)
    graph_builder.add_node("generate_answer", __generate_answer__)
    graph_builder.add_node("retrieved_context_evaluator", __retrieved_context_evaluator__)
    # graph_builder.add_node("evaluate_answer", __evaluate_answer__)
    graph_builder.add_node("save_question_and_answer", __save_question_and_answer__)

    graph_builder.set_conditional_entry_point(__router_choice__, {"vectorstore": "retrieve_context", "llm": "generate_answer"})
    graph_builder.add_edge("retrieve_context", "retrieved_context_evaluator")
    graph_builder.add_edge("retrieved_context_evaluator", "generate_answer")
    graph_builder.add_edge("generate_answer", "save_question_and_answer")
    graph_builder.add_edge("save_question_and_answer", END)

    graph = graph_builder.compile(checkpointer=checkpointer, store=store)

    return graph
