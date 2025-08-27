import os

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph, MessagesState
from typing_extensions import List
from tavily import TavilyClient

from ACD.rag.db import get_db

MODEL = "llama3.1:8b"
TAVILIY_API_KEY_PATH = os.getcwd() + '/ACD/tavily_token'
EVALUATION_RELEVANT = "relevant"
EVALUATION_PARTIALLY_RELEVANT = "partially_relevant"

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

    tavily_token = ""
    with open(TAVILIY_API_KEY_PATH, 'r') as file:
        tavily_token = file.read().strip()

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

def create_graph():
    graph_builder = StateGraph(RagState)
    graph_builder.add_node("retrieve_context", __retrieve_context__)
    graph_builder.add_node("generate_answer", __generate_answer__)
    graph_builder.add_node("retrieved_context_evaluator", __retrieved_context_evaluator__)
    graph_builder.add_node("web_search", __web_search__)

    graph_builder.set_conditional_entry_point(__router_choice__, {"vectorstore": "retrieve_context", "llm": "generate_answer"})
    graph_builder.add_edge("retrieve_context", "retrieved_context_evaluator")
    graph_builder.add_conditional_edges(
        "retrieved_context_evaluator",
        __decision_based_on_evaluation__,
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
