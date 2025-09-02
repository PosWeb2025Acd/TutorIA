from datetime import datetime, timedelta

import jwt
import os

JWT_EXPIRATION_HOURS=int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY")
JWT_ALGORITH="HS256"

def generate_token(user_id, user):
    """
    Gera um token JWT para um usuário autenticado
    """

    payload = {
        'user_id': str(user_id),
        'usuario': user,
        'exp': datetime.now() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.now()
    }
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITH)
