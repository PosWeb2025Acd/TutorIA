def get_question_and_answers_without_evaluation(db_connection):
    """
    Recover all question and answers pairs that does not have an evaluation
    """

    cursor = db_connection.cursor()

    query = """
    select qaa.id, qaa.question, qaa.answer from question_and_answer qaa where qaa.id not in (select e.question_answer_id  from evaluation e );
    """

    cursor.execute(query)
    question_and_answer_list = cursor.fetchall()

    if not question_and_answer_list:
        cursor.close()
        return None
    
    cursor.close()
    
    return question_and_answer_list

