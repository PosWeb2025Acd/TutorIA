def create_user_question_and_answer(db_connection, user_id, question, answer):
    """
    Create register of user question and the answer he received
    """

    cursor = db_connection.cursor()
    try:
        insert_query = """
        INSERT INTO question_and_answer (user_id, question, answer) VALUES (%s, %s, %s)
        """
        cursor.execute(insert_query, (user_id, question, answer))
        db_connection.commit()
    except Exception as e:
        db_connection.rollback()
        raise
    finally:
        cursor.close()
        db_connection.close()
