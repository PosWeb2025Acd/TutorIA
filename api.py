import os
from dotenv import load_dotenv
load_dotenv(os.path.dirname(__file__) + '/.env')

from flask import Flask, Response, request
from ACD.rag.rag import create_graph
from langgraph.checkpoint.postgres import PostgresSaver
import json

PROJECT_NAME = "TutorIA"
INFO = {
    "project_name": PROJECT_NAME,
    "version": "0.0.1",
    "description": "API para o assistente TutorIA",
}
POSTGRES_CONNECTION = 'postgresql://' + os.getenv("POSTGRES_USER") + ':' + os.getenv("POSTGRES_PASSWORD") + '@localhost:5432/' + os.getenv("POSTGRES_DB") + '?sslmode=disable'
service = Flask(PROJECT_NAME)

@service.get("/")
def info():
    return Response(
        json.dumps(INFO),
        status=200,
        mimetype="application/json"
    )

@service.post("/acd/enviar-arquivos")
def acd_upload_files():
    file = request.files["file_to_upload"]
    if not file:
        return Response(
            json.dumps({"status": "error", "message": "No file provided"}),
            status=400,
            mimetype="application/json"
        )

    file.close()

    return Response(
        json.dumps({"status": "success", "message": "Arquivo atualizado com sucesso!"}),
        mimetype="application/json"
    )


@service.post("/acd/resposta")
def acd_ask_and_get_answer():
    request_data = request.get_json()
    question = request_data["question"] if "question" in request_data else ""
    if not question:
        return Response(
            json.dumps({"status": "error", "message": "Informa a sua pergunta"}),
            status=400,
            mimetype="application/json"
        )

    with PostgresSaver.from_conn_string(POSTGRES_CONNECTION) as checkpointer:
        rag = create_graph(checkpointer)
        result = rag.invoke(
            {"messages": [{"role": "user", "content": question}]},
            {"configurable": {"thread_id": "abc123"}},
        )

        answer = result["messages"][-1]
        sources = result["sources"] if "sources" in result else []

        return Response(
            json.dumps({"status": "success", "answer": answer.content, "sources": sources}),
            mimetype="application/json"
        )

if __name__ == "__main__":
    service.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )
