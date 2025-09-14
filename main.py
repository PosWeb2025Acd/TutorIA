import os
from dotenv import load_dotenv
load_dotenv(os.path.dirname(__file__) + '/../.env')
from langgraph.checkpoint.postgres import PostgresSaver
from rag.rag import create_graph
from psycopg import Connection

POSTGRES_CONNECTION = 'postgresql://' + os.getenv("DB_USER") + ':' + os.getenv("DB_PASSWORD") + '@' + os.getenv("DB_HOST") + ':5432/' + os.getenv("DB_NAME") + '?sslmode=disable'

if __name__ == "__main__":
    with Connection.connect(POSTGRES_CONNECTION) as conn:
        checkpointer = PostgresSaver(conn)
        store = None

        graph = create_graph(checkpointer, store)

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
                {"configurable": {"thread_id": "abc123", "user_id": "f977139d-9f1a-4bcb-ada6-e00230928559"}},
            )

            answer = result["messages"][-1]
            sources = result["sources"] if "sources" in result else []

            formated_response = f"Resposta: {answer.content}\nFontes:\n{"\n".join(sources)}"
            print(f"🤖 {formated_response}")
