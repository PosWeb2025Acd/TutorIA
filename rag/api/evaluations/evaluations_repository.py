def get_evaluations_on_db(db_connection, page):
    """
    Get all evaluations from the database with pagination
    """

    cursor = db_connection.cursor()
    offset = (page - 1) * 10
    cursor.execute(
        """
        SELECT e.id, qa.question, qa.answer, u.usuario as "user", e.llm_evaluation_reasoning, e.llm_evaluation_score, e.created_at
        FROM evaluation e
        INNER JOIN question_and_answer qa ON e.question_answer_id = qa.id
        INNER JOIN usuarios u ON qa.user_id = u.id
        ORDER BY created_at DESC
        LIMIT 10 OFFSET %s
        """,
        (offset,)
    )
    evaluations = cursor.fetchall()
    cursor.close()

    return evaluations

def count_evaluations(db_connection):
    """
    Count total evaluations in the database
    """

    cursor = db_connection.cursor()
    query = """
    SELECT COUNT(*) as total FROM evaluation
    """

    cursor.execute(query)
    total_evaluations = cursor.fetchone()["total"]
    cursor.close()

    return total_evaluations
