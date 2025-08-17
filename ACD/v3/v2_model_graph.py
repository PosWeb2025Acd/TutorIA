from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import List, TypedDict

from db import get_db
from process_files import embedding_model

# THIS MODEL DOES NOT ACCEPTS TOLLS
MODEL = "llama3.1:8b"

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

@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """
    Step to retrieve the context from the vector database based on the user question.
    """

    print(f"🤖 Recuperando contexto baseado nos documentos para uma melhor resposta...")
    retrived_context = vector_store.similarity_search(query, k=3)
    serialized = "\n\n".join((f"Content: {doc.page_content}") for doc in retrived_context)
    sources = [doc.id for doc in retrived_context]
    print(f"🤖 Contexto recuperado com sucesso...")

    return serialized, sources

def retrieve_data_or_respond(state: RagState):
    """
    Step to generate the answer based on the retrieved context and the user question.
    """

    llm_with_tools = llm.bind_tools([retrieve_context])
    llm_response = llm_with_tools.invoke(state["messages"])

    # Appending messages to the state
    return {"messages": [llm_response]}

def generate_answer(state: RagState):
    print(f"🤖 Gerando a sua resposta...")

    message_tools = []
    for message in reversed(state["messages"]):
        if message.type == "tool":
            message_tools.append(message)
        else:
            break

    sources = message_tools[-1].artifact
    message_tools = message_tools[::-1]
    retrived_content = "\n\n".join(doc.content for doc in message_tools)
    prompt = create_prompt()
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


def remove_think_set_from_awnser(answer):
    if "</think>" in answer:
        start = answer.index("</think>")
        end = start + len("</think>")
        return answer[end:].strip()

    return answer.strip()

if __name__ == "__main__":
    tools = ToolNode([retrieve_context])
    graph_builder = StateGraph(RagState)
    graph_builder.add_node(retrieve_data_or_respond)
    graph_builder.add_node("retrieve", tools)
    graph_builder.add_node(generate_answer)

    graph_builder.set_entry_point("retrieve_data_or_respond")
    graph_builder.add_conditional_edges(
        "retrieve_data_or_respond",
        tools_condition,
        {END: END, "tools": "retrieve"}
    )
    graph_builder.add_edge("tools", "generate_answer")
    graph_builder.add_edge("generate_answer", END)

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
            {"configurable": {"thread_id": "abc123", "vector_store": vector_store, "llm": llm}},
        )

        answer = result["messages"][-1]
        sources = result["sources"]

        formated_response = f"Resposta: {answer.content}\nFontes:\n{"\n".join(sources)}"
        print(f"🤖 {formated_response}")
