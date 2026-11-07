"""
Testes contra o Postgres real, pois os testes offline não executam o SQL. Não rodam por padrão: use `pytest -m live`.
Tudo roda em uma transação desfeita ao final, então nada fica no banco. Fora do container (onde db-scripts/ existe)
o script também é aplicado na transação; no container, as tabelas precisam já ter sido criadas.
"""

import os
import pathlib

import psycopg
import pytest

from psycopg.rows import dict_row

from api.context_evaluations import context_evaluations_repository as repository

pytestmark = [pytest.mark.live, pytest.mark.skipif(not os.getenv("DB_USER"), reason="DB_* não configuradas")]

SCRIPT = pathlib.Path(__file__).resolve().parents[3] / "db-scripts" / "upgrade_context_evaluation.sql"
EVALUATION = {
    "question": "ignorada",
    "evaluator": "jev",
    "config": {"model": "jev-1.13.0", "min_probability": 0.7},
    "fallback_error": None,
    "chunks": [
        {"position": 1, "document_id": "grafos.pdf:1:0", "content": "outro", "label": "not_relevant", "probability": 0.8, "used": False, "details": {"score": 0.2}},
        {"position": 0, "document_id": "poo.pdf:1:0", "content": "texto", "label": "relevant", "probability": 0.9, "used": True, "details": {"score": 1.9}},
    ],
}

@pytest.fixture
def conn():
    from db.postgres import POSTGRES_CONNECTION

    connection = psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row)
    try:
        if SCRIPT.exists():
            # Duas vezes: o script precisa ser idempotente
            connection.execute(SCRIPT.read_text())
            connection.execute(SCRIPT.read_text())
        yield connection
    finally:
        connection.rollback()
        connection.close()

@pytest.fixture
def question_answer_id(conn):
    user = conn.execute("INSERT INTO usuarios (usuario, senha) VALUES ('teste-live-context-evaluation', 'x') RETURNING id").fetchone()
    return conn.execute(
        "INSERT INTO question_and_answer (user_id, question, answer) VALUES (%s, 'pergunta', 'resposta') RETURNING id",
        (user["id"],),
    ).fetchone()["id"]

def test_round_trip(conn, question_answer_id):
    context_evaluation_id = repository.create_context_evaluation(conn, question_answer_id, EVALUATION)

    evaluations = repository.get_context_evaluations_on_db(conn, 1)

    evaluation = next(item for item in evaluations if item["id"] == context_evaluation_id)
    assert (evaluation["question"], evaluation["answer"], evaluation["user"]) == ("pergunta", "resposta", "teste-live-context-evaluation")
    assert evaluation["evaluator"] == "jev"
    assert evaluation["config"] == EVALUATION["config"]
    assert [chunk["position"] for chunk in evaluation["chunks"]] == [0, 1]
    assert evaluation["chunks"][0]["probability"] == 0.9
    assert evaluation["chunks"][0]["used"] is True
    assert evaluation["chunks"][0]["details"] == {"score": 1.9}

def test_evaluator_filter(conn, question_answer_id):
    llm_evaluation = {**EVALUATION, "evaluator": "llm", "chunks": []}
    before = repository.count_context_evaluations(conn, "llm")

    context_evaluation_id = repository.create_context_evaluation(conn, question_answer_id, llm_evaluation)

    assert repository.count_context_evaluations(conn, "llm") == before + 1
    assert context_evaluation_id in [item["id"] for item in repository.get_context_evaluations_on_db(conn, 1, "llm")]
    assert context_evaluation_id not in [item["id"] for item in repository.get_context_evaluations_on_db(conn, 1, "jev")]

def test_evaluation_needs_an_existing_question_and_answer(conn):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        repository.create_context_evaluation(conn, -1, EVALUATION)

def test_chunk_with_nul_byte_is_saved(conn, question_answer_id):
    chunk = {**EVALUATION["chunks"][0], "content": "armazenados\x00no banco", "details": {"raw_label": "RELE\x00VANT"}}

    context_evaluation_id = repository.create_context_evaluation(conn, question_answer_id, {**EVALUATION, "chunks": [chunk]})

    evaluation = next(item for item in repository.get_context_evaluations_on_db(conn, 1) if item["id"] == context_evaluation_id)
    assert evaluation["chunks"][0]["content"] == "armazenadosno banco"
    assert evaluation["chunks"][0]["details"] == {"raw_label": "RELEVANT"}

