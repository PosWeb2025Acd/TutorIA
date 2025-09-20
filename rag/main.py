from api.acd.acd_controller import get_answer_from_question
from api.evaluations.evaluations_repository import get_evaluations_on_db, count_evaluations
from api.users.user_controller import create_user, login_user
from api.token import generate_token, token_required_as_param
from db.postgres import get_postgres_connection, POSTGRES_CONNECTION
from flask import Flask, Response, request
from langgraph.checkpoint.postgres import PostgresSaver

import json
import logging

from rag import create_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_NAME = "TutorIA"
INFO = {
    "project_name": PROJECT_NAME,
    "version": "0.0.1",
    "description": "API para o assistente TutorIA",
}
service = Flask(PROJECT_NAME)

@service.get("/")
def info():
    return Response(
        json.dumps(INFO),
        status=200,
        mimetype="application/json"
    )

@service.post("/criar-usuario")
def tutor_ia_create_user():
    """
    Endpoint para criar um novo usuário
    """

    conn = get_postgres_connection()
    try:
        data = request.get_json()
        if data is None:
            return Response(
                json.dumps({"erro": "Dados não fornecidos. Envie um JSON válido.", "status": "error"}),
                status=400,
                mimetype="application/json"
            )

        user_created, user_data, message = create_user(conn, data)
        if user_created:
            user_data["id"] = str(user_data["id"])

            return Response(
                json.dumps({"mensagem": message, "status": "success", "usuario": user_data}),
                status=200,
                mimetype="application/json"
            )

        return Response(
            json.dumps({'erro': message, 'status': "error"}),
            status=400,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Erro interno no servidor: {e}")

        return Response(
            json.dumps({"erro": "Erro interno do servidor.", "status": "error"}),
            status=500,
            mimetype="application/json"
        )
    
@service.post("/login")
def tutor_ia_user_login():
    """
    Endpoint para criar um novo usuário
    """

    conn = get_postgres_connection()
    try:
        data = request.get_json()

        if not data:
            return Response(
                json.dumps({"erro": "Dados não fornecidos. Envie um JSON válido.", "status": "error"}),
                status=400,
                mimetype="application/json"
            )

        login_successful, user_data, message = login_user(conn, data)
        if login_successful:
            user_data["id"] = str(user_data["id"])
            user_data["data_criacao"] = user_data["data_criacao"].strftime('%m/%d/%Y %H:%M:%S')

            return Response(
                json.dumps({'mensagem': message, 'status': 'success', 'usuario': user_data, 'token': generate_token(user_data["id"], user_data["usuario"])}),
                status=200,
                mimetype="application/json"
            )

        return Response(
            json.dumps({"status": "error", "error": message}),
            status=401,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Erro interno no servidor: {e}")

        return Response(
            json.dumps({"erro": "Erro interno do servidor.", "status": "error"}),
            status=500,
            mimetype="application/json"
        )

@service.post("/acd/enviar-arquivos")
@token_required_as_param
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
        status=200,
        mimetype="application/json"
    )

@service.post("/acd/resposta")
@token_required_as_param
def acd_ask_and_get_answer(user_auth_data):
    request_data = request.get_json()
    question = request_data["question"] if "question" in request_data else ""
    if not question:
        return Response(
            json.dumps({"status": "error", "message": "Informe a sua pergunta"}),
            status=400,
            mimetype="application/json"
        )

    with PostgresSaver.from_conn_string(POSTGRES_CONNECTION) as checkpointer:
        rag_graph = create_graph(checkpointer)

        success, answer, sources = get_answer_from_question(rag_graph, question, user_auth_data)
        if success:
            return Response(
                json.dumps({"status": "success", "answer": answer, "sources": sources}),
                status=200,
                mimetype="application/json"
            )

        return Response(
            json.dumps({"status": "error", "erro": "Não foi possível obter uma resposta :("}),
            status=500,
            mimetype="application/json"
        )

@service.get("/acd/avaliacoes-resposta")
@token_required_as_param
def acd_get_answer_evaluations(user_auth_data):
    """
    Endpoint para obter todas as avaliações de respostas
    """
    conn = get_postgres_connection()
    try:
        page = int(request.args.get("page", 1))
        if page < 1:
            return Response(
                json.dumps({"erro": "Número de página inválido. Deve ser maior ou igual a 1.", "status": "error"}),
                status=400,
                mimetype="application/json"
            )

        evaluations = get_evaluations_on_db(conn, page)
        total_evaluations = count_evaluations(conn)
        total_pages = (total_evaluations + 9) // 10  # Arredonda para cima a divisão por 10

        if not evaluations:
            return Response(
                json.dumps({"mensagem": "Nenhuma avaliação encontrada.", "status": "success", "evaluation_list": [], "total_evaluations": 0, "total_pages": 0}),
                status=200,
                mimetype="application/json"
            )
        
        evaluations = [{
            "question": eval["question"],
            "answer": eval["answer"],
            "user": eval["user"],
            "score": eval["llm_evaluation_score"],
            "reasoning": eval["llm_evaluation_reasoning"],
            "evaluation_date": eval["created_at"].strftime('%d/%m/%Y %H:%M:%S')
        } for eval in evaluations]

        response = {
            "status": "success",
            "evaluation_list": evaluations,
            "total_evaluations": total_evaluations,
            "total_pages": total_pages
        }

        return Response(
            json.dumps(response, default=str),
            status=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Erro interno no servidor: {e}")

        return Response(
            json.dumps({"erro": "Erro interno do servidor.", "status": "error"}),
            status=500,
            mimetype="application/json"
        )
    finally:
        conn.close()

if __name__ == "__main__":
    service.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )
