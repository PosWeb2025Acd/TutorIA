"""
Testes contra os serviços reais (Ollama local e API da TypeSafe). Não rodam por padrão: use `pytest -m live`.
"""

import os
import urllib.request

import pytest

from rag_graph.context_evaluators import grade_documents_jev, grade_documents_llm
from tests.conftest import make_document

pytestmark = pytest.mark.live

QUESTION = "O que é polimorfismo em programação orientada a objetos?"
RELEVANT = make_document("poo.pdf:1:0", "Polimorfismo é o princípio da orientação a objetos pelo qual objetos de classes diferentes respondem à mesma mensagem, cada um com sua própria implementação do método.")
NOT_RELEVANT = make_document("receita.pdf:1:0", "Para preparar o bolo, misture a farinha, os ovos e o açúcar e asse por 40 minutos a 180 graus.")

def ollama_available():
    try:
        urllib.request.urlopen(os.getenv("OLLAMA_URL", ""), timeout=2)
        return True
    except Exception:
        return False

@pytest.mark.skipif(not os.getenv("TYPESAFE_API_KEY"), reason="TYPESAFE_API_KEY não configurada")
def test_jev_grades_obvious_cases():
    grades = grade_documents_jev(QUESTION, [RELEVANT, NOT_RELEVANT])

    assert grades[0]["label"] == "relevant"
    assert grades[1]["label"] == "not_relevant"

@pytest.mark.skipif(not ollama_available(), reason="Ollama indisponível em OLLAMA_URL")
def test_llm_grades_obvious_cases():
    grades = grade_documents_llm(QUESTION, [RELEVANT, NOT_RELEVANT])

    assert grades[0]["label"] == "relevant"
    assert grades[1]["label"] == "not_relevant"
