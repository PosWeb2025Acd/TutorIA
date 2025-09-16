def get_answer_from_question(rag_graph, question: str, user_data: dict):
    """
    Utiliza a pergunta para e passa para o sistema RAG para geração de uma resposta
    """
    result = rag_graph.invoke(
        {"messages": [{"role": "user", "content": question}]},
        {"configurable": {"thread_id": user_data["user_session_id"], "user_id": user_data["user_id"]}},
    )

    answer = result["messages"][-1]
    sources = result["sources"] if "sources" in result else []

    return True, answer.content, sources
