import os
from dotenv import load_dotenv
load_dotenv(os.path.dirname(__file__) + '/.env')
from langgraph.checkpoint.postgres import PostgresSaver
from rag.rag import create_graph

POSTGRES_CONNECTION = 'postgresql://' + os.getenv("DB_USER") + ':' + os.getenv("DB_PASSWORD") + '@localhost:5432/' + os.getenv("DB_NAME") + '?sslmode=disable'

if __name__ == "__main__":
    with PostgresSaver.from_conn_string(POSTGRES_CONNECTION) as checkpointer:
        # checkpointer.setup()

        graph = create_graph(checkpointer=checkpointer)

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
