# Based on tutorial from the langchain library https://python.langchain.com/docs/tutorials/rag/
# Embedding model: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 (Modelo especializado em busca por similaridade de texto)
# -- Modelo cria um vetores com 384 dimensões

# from model_graph import create_graph
from model_graph import create_graph

MODEL = "deepseek-r1:8b"

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
