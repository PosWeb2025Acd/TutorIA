from psycopg.types.json import Jsonb

from db.postgres import get_postgres_connection

PAGE_SIZE = 10

def create_context_evaluation(db_connection, question_answer_id, evaluation):
    """
    Insere a avaliação e seus chunks. Não faz commit: quem abre a conexão controla a transação.
    """

    cursor = db_connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO context_evaluation (question_answer_id, evaluator, config, fallback_error)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (question_answer_id, evaluation["evaluator"], Jsonb(evaluation["config"]), evaluation["fallback_error"]),
        )
        context_evaluation_id = cursor.fetchone()["id"]

        cursor.executemany(
            """
            INSERT INTO context_evaluation_chunk (context_evaluation_id, position, document_id, content, label, probability, used, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (context_evaluation_id, chunk["position"], chunk["document_id"], chunk["content"], chunk["label"], chunk["probability"], chunk["used"], Jsonb(chunk["details"]))
                for chunk in evaluation["chunks"]
            ],
        )
    finally:
        cursor.close()

    return context_evaluation_id

def get_context_evaluations_on_db(db_connection, page, evaluator=None):
    """
    Retorna uma página de avaliações, das mais recentes para as mais antigas, cada uma com seus chunks em "chunks".
    """

    cursor = db_connection.cursor()
    try:
        cursor.execute(
            """
            SELECT e.id, qa.question, qa.answer, u.usuario AS "user", e.evaluator, e.config, e.fallback_error, e.created_at
            FROM context_evaluation e
            INNER JOIN question_and_answer qa ON e.question_answer_id = qa.id
            INNER JOIN usuarios u ON qa.user_id = u.id
            WHERE %(evaluator)s::text IS NULL OR e.evaluator = %(evaluator)s
            ORDER BY e.created_at DESC, e.id DESC
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            {"evaluator": evaluator, "limit": PAGE_SIZE, "offset": (page - 1) * PAGE_SIZE},
        )
        evaluations = cursor.fetchall()

        cursor.execute(
            """
            SELECT context_evaluation_id, position, document_id, content, label, probability, used, details
            FROM context_evaluation_chunk
            WHERE context_evaluation_id = ANY(%s)
            ORDER BY context_evaluation_id, position
            """,
            ([evaluation["id"] for evaluation in evaluations],),
        )
        chunks = cursor.fetchall()
    finally:
        cursor.close()

    for evaluation in evaluations:
        evaluation["chunks"] = [chunk for chunk in chunks if chunk["context_evaluation_id"] == evaluation["id"]]

    return evaluations

def count_context_evaluations(db_connection, evaluator=None):
    """
    Conta as avaliações, opcionalmente de um único avaliador
    """

    cursor = db_connection.cursor()
    try:
        cursor.execute(
            """
            SELECT COUNT(*) AS total FROM context_evaluation
            WHERE %(evaluator)s::text IS NULL OR evaluator = %(evaluator)s
            """,
            {"evaluator": evaluator},
        )
        return cursor.fetchone()["total"]
    finally:
        cursor.close()

class PostgresContextEvaluationRecorder:
    """
    Guarda as avaliações no Postgres. A avaliação e seus chunks entram na mesma transação.
    """

    def record(self, question_answer_id: int, evaluation: dict) -> None:
        with get_postgres_connection() as conn:
            create_context_evaluation(conn, question_answer_id, evaluation)
