from flask import Response
from functools import wraps

import json

def admin_validate(f):
    @wraps(f)
    def validate_admin_user(user_auth_data, *args, **kwargs):
        user_admin = user_auth_data["admin"] if "admin" in user_auth_data else False
        if not user_admin:
            return Response(
                json.dumps({"erro": "Não tem as permissões necessárias para acessar a página", "status": "error"}),
                status=403,
                mimetype="application/json"
            )

        return f(user_auth_data, *args, **kwargs)

    return validate_admin_user
