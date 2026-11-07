def create_user_question_and_answer(db_connection, user_id, question, answer):
    """
    Create register of user question and the answer they received, returning its id
    """

    cursor = db_connection.cursor()
    try:
        insert_query = """
        INSERT INTO question_and_answer (user_id, question, answer) VALUES (%s, %s, %s) RETURNING id
        """
        cursor.execute(insert_query, (user_id, question, answer))
        question_answer_id = cursor.fetchone()["id"]
        db_connection.commit()

        return question_answer_id
    except Exception as e:
        db_connection.rollback()
        raise
    finally:
        cursor.close()
        db_connection.close()
