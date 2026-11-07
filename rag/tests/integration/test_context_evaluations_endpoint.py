from datetime import datetime
from unittest.mock import MagicMock

import pytest

import main
from api import token

ADMIN = {"id": "f977139d-9f1a-4bcb-ada6-e00230928559", "usuario": "admin", "is_admin": True, "admin": True}
STUDENT = {"id": "a977139d-9f1a-4bcb-ada6-e00230928559", "usuario": "aluno", "is_admin": False, "admin": False}
ROW = {
    "id": 7,
    "question": "O que é polimorfismo?",
    "answer": "É a capacidade de...",
    "user": "aluno",
    "evaluator": "jev",
    "config": {"model": "jev-1.13.0", "min_probability": 0.7},
    "fallback_error": None,
    "created_at": datetime(2026, 11, 7, 12, 30, 0),
    "chunks": [{
        "context_evaluation_id": 7,
        "position": 0,
        "document_id": "poo.pdf:1:0",
        "content": "texto do chunk",
        "label": "relevant",
        "probability": 0.9,
        "used": True,
        "details": {"score": 1.9},
    }],
}

@pytest.fixture
def repository(monkeypatch):
    monkeypatch.setattr(token, "JWT_SECRET_KEY", "segredo-de-teste")
    monkeypatch.setattr(token, "get_postgres_connection", MagicMock())
    monkeypatch.setattr(main, "get_postgres_connection", MagicMock())

    get = MagicMock(return_value=[ROW])
    count = MagicMock(return_value=11)
    monkeypatch.setattr(main, "get_context_evaluations_on_db", get)
    monkeypatch.setattr(main, "count_context_evaluations", count)

    return type("Repository", (), {"get": get, "count": count})

def request_as(monkeypatch, user, query=""):
    monkeypatch.setattr(token, "get_user_by_id_and_user", lambda conn, user_id, username: user)
    headers = {"Authorization": f"Bearer {token.generate_token(user)}"}

    return main.service.test_client().get(f"/acd/avaliacoes-contexto{query}", headers=headers)

def test_returns_the_evaluations_with_their_chunks(monkeypatch, repository):
    response = request_as(monkeypatch, ADMIN)

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "success"
    assert body["total_evaluations"] == 11
    assert body["total_pages"] == 2
    assert body["evaluation_list"] == [{
        "id": 7,
        "question": "O que é polimorfismo?",
        "answer": "É a capacidade de...",
        "user": "aluno",
        "evaluator": "jev",
        "config": {"model": "jev-1.13.0", "min_probability": 0.7},
        "fallback_error": None,
        "evaluation_date": "07/11/2026 12:30:00",
        "chunks": [{
            "position": 0,
            "document_id": "poo.pdf:1:0",
            "content": "texto do chunk",
            "label": "relevant",
            "probability": 0.9,
            "used": True,
            "details": {"score": 1.9},
        }],
    }]

def test_passes_page_and_evaluator_to_the_repository(monkeypatch, repository):
    request_as(monkeypatch, ADMIN, "?page=2&evaluator=llm")

    assert repository.get.call_args.args[1:] == (2, "llm")
    assert repository.count.call_args.args[1:] == ("llm",)

def test_page_and_evaluator_are_optional(monkeypatch, repository):
    request_as(monkeypatch, ADMIN)

    assert repository.get.call_args.args[1:] == (1, None)

def test_empty_result(monkeypatch, repository):
    repository.get.return_value = []
    repository.count.return_value = 0

    body = request_as(monkeypatch, ADMIN).get_json()

    assert (body["evaluation_list"], body["total_evaluations"], body["total_pages"]) == ([], 0, 0)

@pytest.mark.parametrize("page", ["0", "-1", "abc", "1.5"])
def test_invalid_page_returns_400(monkeypatch, repository, page):
    response = request_as(monkeypatch, ADMIN, f"?page={page}")

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"
    assert "erro" in response.get_json()
    repository.get.assert_not_called()

def test_student_gets_403(monkeypatch, repository):
    response = request_as(monkeypatch, STUDENT)

    assert response.status_code == 403
    repository.get.assert_not_called()

def test_missing_token_gets_403(repository):
    response = main.service.test_client().get("/acd/avaliacoes-contexto")

    assert response.status_code == 403
    repository.get.assert_not_called()

def test_repository_failure_returns_500(monkeypatch, repository):
    repository.get.side_effect = RuntimeError("banco indisponível")

    response = request_as(monkeypatch, ADMIN)

    assert response.status_code == 500
    assert response.get_json() == {"erro": "Erro interno do servidor.", "status": "error"}
