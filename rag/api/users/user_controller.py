from rag.api.users.user_repository import create, get_user
from werkzeug.security import generate_password_hash, check_password_hash

def create_user(db_connection, user_data):
    """
    Função para a validação e criação de um novo usuário
    """

    missing_fields = __validate_user_data__(user_data)
    if missing_fields:
        return False, None, f'Campos obrigatórios ausentes: {", ".join(missing_fields)}'

    user = user_data['usuario'].strip()
    password = user_data['senha']

    if len(user) < 3:
        return False, None, 'O nome de usuário deve ter pelo menos 3 caracteres'

    password_hash = generate_password_hash(password)

    return create(db_connection, user, password_hash)

def login_user(db_connection, user_data):
    """
    Realiza o login do usuário
    """

    missing_fields = __validate_user_data__(user_data)
    if missing_fields:
        return False, None, f'Campos obrigatórios ausentes: {", ".join(missing_fields)}'
    
    user = user_data["usuario"].strip()
    password = user_data["senha"]

    user_found = get_user(db_connection, user)
    if not user_found:
        return False, None, "Credenciais inválidas"
    
    if not check_password_hash(user_found["senha"], password):
        return False, None, "Credenciais inválidas"
    
    return True, {"id": user_found["id"], "usuario": user_found["usuario"], "data_criacao": user_found["data_criacao"]}, "Login Feito"

def __validate_user_data__(data):
    """
    Valida os dados obrigatórios do usuário
    """

    required_fields = ['usuario', 'senha']
    missing_fields = []

    for field in required_fields:
        if field not in data or not data[field] or not data[field].strip():
            missing_fields.append(field)

    return missing_fields
