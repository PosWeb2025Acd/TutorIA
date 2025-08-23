import os

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph, MessagesState
from typing_extensions import List
from tavily import TavilyClient

from db import get_db

# THIS MODEL DOES NOT ACCEPTS TOLLS
MODEL = "llama3.1:8b"
TAVILIY_API_KEY_PATH = os.getcwd() + '/tavily_token'
RELEVANT_DOCUMENTS_THRESHOLD = 95
NOT_RELEVANT_DOCUMENTS_THRESHOLD = 80

tavily_token = ""
with open(TAVILIY_API_KEY_PATH, 'r') as file:
    tavily_token = file.read().strip()

tavily_client = TavilyClient(api_key=tavily_token)

llm = ChatOllama(model=MODEL, verbose=False, temperature=0.0)
vector_store = get_db()

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

    sources: List[str]  # List of source document IDs or titles
    documents: List[Document]  # List of document contents
    web_search_recomended: bool

def router_choice(state: RagState):
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

def retrieve_context(state: RagState):
    """
    Step to retrieve the context from the vector database based on the user question.
    """

    retriever = vector_store.as_retriever()

    print(f"🤖 Recuperando contexto baseado nos documentos para uma melhor resposta...")
    question = state["messages"][-1].content
    documents = retriever.invoke(question)
    print(f"🤖 Contexto recuperado com sucesso...")

    return {"documents": documents, "sources": [doc.id for doc in documents]}

def retrieved_context_evaluator(state: RagState):
    print (f"🤖 Avaliando a qualidade do contexto recuperado...")

    prompt_data = """
    You are a grader assessing relevance of a retrieved document to a user question.
    Given a user question and retrieved document, determine if the document provider has sufficient context to answer the question accurately.
    To evaluate if the document is relevant, you can check if the document contains keywords related to the user question.
    It does not need to be a stringent test. The goal is to filter out erroneous retrievals
    Give a binary score 'relevant' or 'not_relevant' to indicate wheter the document is relevant to the question
    Provide the binary score as a JSON with a single key 'evaluation' and no premable or explaination
    Document to be used for evaluation: {documents}
    Here is the user question: {question}
    """

    prompt = PromptTemplate.from_template(prompt_data)
    retrieval_grader = prompt | llm | JsonOutputParser()
    question = state["messages"][-1].content

    filtered_documents = []
    for doc in state["documents"]:
        result = retrieval_grader.invoke({
            "question": question,
            "documents": doc.page_content,
        })

        evaluation = result['evaluation'].lower()
        print(f"🤖 Avaliação do documento {doc.id}: {evaluation}")

        if evaluation in ['relevant', 'partially_relevant']:
            filtered_documents.append(doc)

    web_search_recomended = False if len(filtered_documents) > 0 else True

    return {"documents": filtered_documents, "sources": [doc.id for doc in filtered_documents], "web_search_recomended": web_search_recomended}

def decision_based_on_evaluation(state: RagState):
    """
    Step to decide whether to generate an answer based on the retrieved context or to perform a web search.
    """
    web_search_recomended = state["web_search_recomended"]
    if web_search_recomended:
        print("🤖 A avaliação do contexto recuperado indicou que uma busca na web pode ser útil para complementar a resposta.")
        return "web_search"

    print("🤖 A avaliação do contexto recuperado indicou que é possível gerar uma resposta com o contexto disponível.")
    return "generate_answer"

def generate_answer(state: RagState):
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
    retrived_content = "\n\n".join(doc for doc in message_tools)
    prompt_messages = prompt.invoke({"context": retrived_content})

    conversation = [
        message
        for message in state["messages"]
        if message.type in ("human", "system")
        or (message.type == "ai" and not message.tool_calls)
    ]

    prompt = prompt_messages.to_messages() + conversation

    response = llm.invoke(prompt)
    
    return {"messages": [response], "sources": sources}

def web_search(state: RagState):
    print (f"🤖 Realizando uma busca na web para complementar a resposta...")

    print (f"🤖 A busca pode demorar um pouco, por favor aguarde...")

    print (f"🤖 Busca na web finalizada...")

def remove_think_set_from_awnser(answer):
    if "</think>" in answer:
        start = answer.index("</think>")
        end = start + len("</think>")
        return answer[end:].strip()

    return answer.strip()

def create_graph():
    graph_builder = StateGraph(RagState)
    graph_builder.add_node("retrieve_context", retrieve_context)
    graph_builder.add_node("generate_answer", generate_answer)
    graph_builder.add_node("retrieved_context_evaluator", retrieved_context_evaluator)
    graph_builder.add_node("web_search", web_search)

    graph_builder.set_conditional_entry_point(router_choice, {"vectorstore": "retrieve_context", "llm": "generate_answer"})
    graph_builder.add_edge("retrieve_context", "retrieved_context_evaluator")
    graph_builder.add_conditional_edges(
        "retrieved_context_evaluator",
        decision_based_on_evaluation,
        {
            "web_search": "web_search",
            "generate_answer": "generate_answer",
        },
    )
    graph_builder.add_edge("web_search", "generate_answer")
    graph_builder.add_edge("generate_answer", END)

    memory = InMemorySaver()
    graph = graph_builder.compile(checkpointer=memory)

    return graph

if __name__ == "__main__":
    graph = create_graph()

    while True:
        user_question = input("👤 Digite a sua pergunta (Para finalizar, digite \"sair\"): ")
        if not user_question.strip():
            print("Por favor, digite uma pergunta.")
            continue

        if user_question.strip().lower() == "sair":
            print("🤖 Saindo do assistente. Até logo!")
            break

        result = graph.invoke(
            {"messages": [{"role": "user", "content": user_question}]},
            {"configurable": {"thread_id": "abc123"}},
        )

        answer = result["messages"][-1]
        sources = result["sources"] if "sources" in result else []

        formated_response = f"Resposta: {answer.content}\nFontes:\n{"\n".join(sources)}"
        print(f"🤖 {formated_response}")
