import os
from dotenv import load_dotenv
load_dotenv(os.path.dirname(__file__) + '/.env')

from api.postgres import get_db_connection
from api.users.user_controller import create_user, login_user
from api.token import generate_token, token_required_as_param
from api.acd.acd_controller import get_answer_from_question
from flask import Flask, Response, request, jsonify

import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_NAME = "TutorIA"
INFO = {
    "project_name": PROJECT_NAME,
    "version": "0.0.1",
    "description": "API para o assistente TutorIA",
}
service = Flask(PROJECT_NAME)
conn = get_db_connection()

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
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'erro': 'Dados não fornecidos. Envie um JSON válido.',
                'status': 'error'
            }), 400

        user_created, user_data, message = create_user(conn, data)
        if user_created:
            return jsonify({
                'mensagem': message,
                'status': 'success',
                'usuario': user_data
            }), 200

        return jsonify({
            "status": "error",
            "error": message
        }), 400

    except Exception as e:
        logger.error(f"Erro interno no servidor: {e}")

        return jsonify({
            'erro': 'Erro interno do servidor',
            'status': 'error'
        }), 500
    
@service.post("/login")
def tutor_ia_user_login():
    """
    Endpoint para criar um novo usuário
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'erro': 'Dados não fornecidos. Envie um JSON válido.',
                'status': 'error'
            }), 400

        login_successful, user_data, message = login_user(conn, data)
        if login_successful:
            return jsonify({
                'mensagem': message,
                'status': 'success',
                'usuario': user_data,
                'token': generate_token(user_data["id"], user_data["usuario"])
            }), 200

        return jsonify({
            "status": "error",
            "error": message
        }), 401

    except Exception as e:
        logger.error(f"Erro interno no servidor: {e}")

        return jsonify({
            'erro': 'Erro interno do servidor',
            'status': 'error'
        }), 500

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

    success, answer, sources = get_answer_from_question(question, user_auth_data)
    if success:
        return Response(
            json.dumps({"status": "success", "answer": answer, "sources": sources}),
            mimetype="application/json"
        )

    return Response(
        json.dumps({"status": "error", "erro": "Não foi possível obter uma resposta :("}),
        mimetype="application/json"
    ), 500

if __name__ == "__main__":
    service.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )
