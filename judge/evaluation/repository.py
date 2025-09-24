def create_evaluation_on_db(db_connection, question_answer_id, llm_reasoning, llm_score):
    """
    Create register of user question and the answer he received
    """

    cursor = db_connection.cursor()
    try:
        insert_query = """
        INSERT INTO evaluation (question_answer_id, llm_evaluation_reasoning, llm_evaluation_score) VALUES (%s, %s, %s)
        """
        cursor.execute(insert_query, (question_answer_id, llm_reasoning, llm_score))
        db_connection.commit()
    except Exception as e:
        db_connection.rollback()
        raise
    finally:
        cursor.close()
