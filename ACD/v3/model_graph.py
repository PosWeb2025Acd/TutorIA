from langchain_core.documents import Document
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain.tools.retriever import create_retriever_tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph, MessagesState
from typing_extensions import List

from db import get_db
from process_files import embedding_model

MODEL = "deepseek-r1:8b"

llm = ChatOllama(model=MODEL, verbose=False, temperature=0.0)
vector_store = get_db(embedding_model())

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

    # question: str
    context: List[Document]
    sources: List[str]  # List of source document IDs or titles

def create_prompt():
    prompt = """
    You are an assistant for question-answering tasks related to computer science.
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
    Context: {context}
    Think this step by step and provide a concise answer.
    """

    return ChatPromptTemplate.from_messages([("system", prompt)])

def retrieve_context(state: RagState):
    """
    Step to retrieve the context from the vector database based on the user question.
    """

    print(f"🤖 Recuperando contexto baseado nos documentos para uma melhor resposta...")

    question = state["messages"][-1]
    retrived_context = vector_store.similarity_search(question.content, k=3)

    print(f"🤖 Contexto recuperado com sucesso...")

    return {"context": retrived_context, "sources": [doc.id for doc in retrived_context]}

def generate_answer(state: RagState):
    """
    Step to generate the answer based on the retrieved context and the user question.
    """
    print(f"🤖 Pensando sobre a resposta...")

    context = "\n\n".join([doc.page_content for doc in state["context"]])
    prompt_template = create_prompt()
    prompt_value = prompt_template.invoke({"question": state["messages"][-1].content, "context": context})
    conversation = [
        message
        for message in state["messages"]
        if message.type in ("human", "system")
        or (message.type == "ai" and message.content not in state["context"])
    ]
    prompt = prompt_value.to_messages() + conversation

    llm_response = llm.invoke(prompt)

    return {"messages": [llm_response]}

def remove_think_set_from_awnser(answer):
    if "</think>" in answer:
        start = answer.index("</think>")
        end = start + len("</think>")
        return answer[end:].strip()

    return answer.strip()

if __name__ == "__main__":
    graph_builder = StateGraph(RagState).add_sequence([retrieve_context, generate_answer])

    graph_builder.add_edge(START, "retrieve_context") # Entrypoint: Each time the graph is invoked, it starts from this node
    graph_builder.add_edge("generate_answer", END) # Workflow finishes when it reaches this node

    memory = InMemorySaver()
    graph = graph_builder.compile(checkpointer=memory)

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
        sources = result["sources"]

        formated_response = f"Resposta: {remove_think_set_from_awnser(answer.content)}\nFontes:\n{"\n".join(sources)}"

        print(f"🤖 {formated_response}")
