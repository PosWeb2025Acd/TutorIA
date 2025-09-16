from rag.rag import create_graph
from db.postgres import POSTGRES_CONNECTION
from langgraph.checkpoint.postgres import PostgresSaver

def get_answer_from_question(question: str, user_data: dict):
    """
    Utiliza a pergunta para e passa para o sistema RAG para geração de uma resposta
    """

    with PostgresSaver.from_conn_string(POSTGRES_CONNECTION) as checkpointer:
        # checkpointer.setup()
        rag = create_graph(checkpointer)
        result = rag.invoke(
            {"messages": [{"role": "user", "content": question}]},
            {"configurable": {"thread_id": user_data["user_session_id"], "user_id": user_data["user_id"]}},
        )

        answer = result["messages"][-1]
        sources = result["sources"] if "sources" in result else []

        return True, answer.content, sources
