from datetime import datetime, timedelta
from db.postgres import get_postgres_connection
from flask import request, jsonify
from functools import wraps
from .users.user_repository import get_user_by_id_and_user

import jwt
import os
import uuid

JWT_EXPIRATION_HOURS=int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY")
JWT_ALGORITH="HS256"

def generate_token(user_id, user):
    """
    Gera um token JWT para um usuário autenticado
    """

    user_id = str(user_id)
    user_session_id = str(uuid.uuid4())

    payload = {
        'user_id': user_id,
        'user': user,
        'user_session_id': user_session_id,
        'exp': datetime.now() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.now()
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITH)

def decode_token(token):
    """
    Faz a decodificação do token e recupera o payload
    """

    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITH])

def token_required_as_param(f):
    """
    Decorator que espera o token como parâmetro da função
    A função decorada deve aceitar 'token' como primeiro parâmetro
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        authorization_header = request.headers.get('Authorization')
        
        if not authorization_header:
            return jsonify({
                'erro': 'Token de acesso requerido no header Authorization',
                'status': 'error'
            }), 403
        
        token = __extract_token_from_header__(authorization_header)
        
        if not token:
            return jsonify({
                'erro': 'Formato do token inválido. Use: Bearer <token>',
                'status': 'error'
            }), 403

        try:
            payload = decode_token(token)
        except Exception as e:
            return jsonify({
                'status': 'error',
                'erro': f"Não foi possível decodificar o token: {str(e)}"
            }), 500
        
        if payload is None:
            return jsonify({
                'erro': 'Token inválido',
                'status': 'error'
            }), 403

        user_found = get_user_by_id_and_user(get_postgres_connection(), payload.get('user_id'), payload.get('user'))
        if user_found is None:
            return jsonify({
                'erro': 'Usuário do token não encontrado',
                'status': 'error'
            }), 403

        return f(payload, *args, **kwargs)
    
    return decorated_function

def __extract_token_from_header__(authorization_header):
    """Extrai token do header Authorization no formato Bearer"""
    if not authorization_header:
        return None

    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None

    return parts[1]
