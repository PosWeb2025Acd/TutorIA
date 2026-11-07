from datetime import datetime
from unittest.mock import MagicMock

import pytest

from psycopg.types.json import Jsonb

from api.context_evaluations import context_evaluations_repository as repository
from api.user_and_answer.user_and_answer_repository import create_user_question_and_answer

EVALUATION = {
    "question": "O que é polimorfismo?",
    "evaluator": "jev",
    "config": {"model": "jev-1.13.0"},
    "fallback_error": None,
    "chunks": [
        {"position": 0, "document_id": "poo.pdf:1:0", "content": "texto", "label": "relevant", "probability": 0.9, "used": True, "details": {"score": 1.9}},
        {"position": 1, "document_id": "grafos.pdf:1:0", "content": "outro", "label": "not_relevant", "probability": 0.8, "used": False, "details": {"score": 0.2}},
    ],
}

def connection_with(cursor):
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn

def test_create_inserts_the_evaluation_and_each_chunk():
    cursor = MagicMock()
    cursor.fetchone.return_value = {"id": 7}

    context_evaluation_id = repository.create_context_evaluation(connection_with(cursor), 42, EVALUATION)

    assert context_evaluation_id == 7
    run_params = cursor.execute.call_args.args[1]
    assert run_params[0:2] == (42, "jev")
    assert isinstance(run_params[2], Jsonb) and run_params[2].obj == {"model": "jev-1.13.0"}
    assert run_params[3] is None

    chunk_rows = cursor.executemany.call_args.args[1]
    assert [row[:7] for row in chunk_rows] == [
        (7, 0, "poo.pdf:1:0", "texto", "relevant", 0.9, True),
        (7, 1, "grafos.pdf:1:0", "outro", "not_relevant", 0.8, False),
    ]
    assert chunk_rows[0][7].obj == {"score": 1.9}
    cursor.close.assert_called_once()

def test_create_does_not_persist_the_question_nor_commit():
    cursor = MagicMock()
    cursor.fetchone.return_value = {"id": 7}
    conn = connection_with(cursor)

    repository.create_context_evaluation(conn, 42, EVALUATION)

    assert "O que é polimorfismo?" not in cursor.execute.call_args.args[1]
    conn.commit.assert_not_called()

def test_recorder_runs_inside_the_connection_transaction(monkeypatch):
    cursor = MagicMock()
    cursor.fetchone.return_value = {"id": 7}
    conn = MagicMock()
    conn.__enter__.return_value = connection_with(cursor)
    monkeypatch.setattr(repository, "get_postgres_connection", lambda: conn)

    repository.PostgresContextEvaluationRecorder().record(42, EVALUATION)

    conn.__enter__.assert_called_once()
    assert conn.__exit__.call_args.args[0] is None
    cursor.executemany.assert_called_once()

def test_recorder_failure_reaches_the_transaction_and_propagates(monkeypatch):
    cursor = MagicMock()
    cursor.fetchone.return_value = {"id": 7}
    cursor.executemany.side_effect = RuntimeError("falha ao inserir os chunks")
    conn = MagicMock()
    conn.__enter__.return_value = connection_with(cursor)
    conn.__exit__.return_value = False
    monkeypatch.setattr(repository, "get_postgres_connection", lambda: conn)

    with pytest.raises(RuntimeError):
        repository.PostgresContextEvaluationRecorder().record(42, EVALUATION)

    # O context manager da conexão do psycopg faz rollback ao receber a exceção
    assert conn.__exit__.call_args.args[0] is RuntimeError

@pytest.mark.parametrize("page, offset", [(1, 0), (3, 20)])
def test_get_paginates_and_filters(page, offset):
    cursor = MagicMock()
    cursor.fetchall.side_effect = [[], []]

    repository.get_context_evaluations_on_db(connection_with(cursor), page, "jev")

    assert cursor.execute.call_args_list[0].args[1] == {"evaluator": "jev", "limit": repository.PAGE_SIZE, "offset": offset}

def test_get_groups_chunks_under_their_evaluation():
    cursor = MagicMock()
    cursor.fetchall.side_effect = [
        [{"id": 2, "created_at": datetime(2026, 11, 7)}, {"id": 1, "created_at": datetime(2026, 11, 6)}],
        [{"context_evaluation_id": 1, "position": 0}, {"context_evaluation_id": 2, "position": 0}, {"context_evaluation_id": 2, "position": 1}],
    ]

    evaluations = repository.get_context_evaluations_on_db(connection_with(cursor), 1)

    assert cursor.execute.call_args_list[1].args[1] == ([2, 1],)
    assert [len(evaluation["chunks"]) for evaluation in evaluations] == [2, 1]

def test_count_passes_the_filter():
    cursor = MagicMock()
    cursor.fetchone.return_value = {"total": 3}

    assert repository.count_context_evaluations(connection_with(cursor), "llm") == 3
    assert cursor.execute.call_args.args[1] == {"evaluator": "llm"}

def test_saving_the_question_and_answer_returns_its_id():
    cursor = MagicMock()
    cursor.fetchone.return_value = {"id": 42}
    conn = connection_with(cursor)

    assert create_user_question_and_answer(conn, "user", "pergunta", "resposta") == 42
    conn.commit.assert_called_once()
    conn.close.assert_called_once()
