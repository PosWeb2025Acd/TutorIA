import psycopg

from datetime import datetime

def create(db_connection, user, password):
    """
    Criação de novo usuário no banco de dados
    """

    cursor = db_connection.cursor()

    try:
        # Verificar se usuário já existe
        cursor.execute("SELECT id FROM usuarios WHERE usuario = %s", (user,))
        if cursor.fetchone():
            return False, None, "Nome de usuário já existe"

        # Inserir novo usuário
        insert_query = """
            INSERT INTO usuarios (usuario, senha, data_criacao)
            VALUES (%s, %s, %s)
            RETURNING id, usuario, data_criacao
        """

        cursor.execute(insert_query, (user, password, datetime.now()))
        result = cursor.fetchone()

        db_connection.commit()

        return True, {
            'id': str(result[0]),
            'usuario': result[1],
            'data_criacao': result[2].isoformat()
        }, "Usuário criado com sucesso"
    except psycopg.IntegrityError as e:
        db_connection.rollback()
        return False, None, "Nome de usuário já existe"
    except Exception as e:
        db_connection.rollback()
        raise
    finally:
        cursor.close()
        db_connection.close()
