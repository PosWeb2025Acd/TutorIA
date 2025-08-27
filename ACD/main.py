from rag.llm_graph import create_graph

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
