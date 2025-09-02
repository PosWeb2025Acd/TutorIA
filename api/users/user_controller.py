from api.users.user_repository import create
from werkzeug.security import generate_password_hash

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
