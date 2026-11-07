from langchain_core.documents import Document
from typing_extensions import List, Protocol

# Campos da avaliação que viram colunas; o restante, específico de cada avaliador, vai para "details"
COMMON_GRADE_FIELDS = ("label", "probability")

class ContextEvaluationRecorder(Protocol):
    """
    Onde as avaliações de contexto são guardadas. O grafo depende apenas desta interface, não do banco.
    """

    def record(self, question_answer_id: int, evaluation: dict) -> None: ...

def build_context_evaluation(
    question: str,
    evaluator: str,
    config: dict,
    documents: List[Document],
    grades: List[dict],
    used_ids: List[str],
    fallback_error: str = None,
) -> dict:
    """
    Monta o registro de uma avaliação, com todos os documentos recuperados, inclusive os descartados.
    O registro passa pelo estado do grafo (salvo no checkpoint), por isso é um dict simples.

    question: serve só para conferir se o registro é do turno atual; não é persistido, pois já está em question_and_answer.
    used_ids: ids dos documentos que entraram no contexto da resposta.
    """

    return {
        "question": question,
        "evaluator": evaluator,
        "config": config,
        "fallback_error": fallback_error,
        "chunks": [
            {
                "position": position,
                "document_id": document.id,
                "content": document.page_content,
                "label": grade["label"],
                "probability": grade.get("probability"),
                "used": document.id in used_ids,
                "details": {key: value for key, value in grade.items() if key not in COMMON_GRADE_FIELDS},
            }
            for position, (document, grade) in enumerate(zip(documents, grades))
        ],
    }
