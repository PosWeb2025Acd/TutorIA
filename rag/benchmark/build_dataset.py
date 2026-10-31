"""
Gera o dataset para anotação manual: para cada pergunta, recupera os chunks com o mesmo retriever do grafo
e grava um CSV com a coluna gold_label vazia.

Uso (dentro do container rag): python -m benchmark.build_dataset [--force]
"""

import argparse
import csv
import json
import os
import re
import time

BENCHMARK_DIR = os.path.dirname(__file__)
QUESTIONS_PATH = os.path.join(BENCHMARK_DIR, "data", "questions.json")
DATASET_PATH = os.path.join(BENCHMARK_DIR, "data", "dataset.csv")
RETRIEVAL_TIMES_PATH = os.path.join(BENCHMARK_DIR, "data", "retrieval_times.json")
DATASET_FIELDS = ["question_id", "question_type", "question", "chunk_id", "chunk_text", "lang", "gold_label"]

PT_WORDS = {"de", "que", "não", "uma", "para", "com", "os", "das", "dos", "são", "como", "mais", "pelo", "pela", "também", "ou", "em", "ao", "à"}
EN_WORDS = {"the", "of", "and", "to", "is", "that", "for", "with", "are", "as", "this", "by", "be", "on", "which", "or", "an", "from"}

def detect_language(text: str) -> str:
    """
    Heurística simples por palavras frequentes, suficiente para separar os chunks em PT e EN no relatório.
    """

    words = re.findall(r"[a-zà-ú]+", text.lower())
    pt = sum(word in PT_WORDS for word in words)
    en = sum(word in EN_WORDS for word in words)

    return "en" if en > pt else "pt"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="sobrescreve um dataset existente (perde a anotação)")
    args = parser.parse_args()

    if os.path.exists(DATASET_PATH) and not args.force:
        raise SystemExit(f"{DATASET_PATH} já existe. Use --force para sobrescrever (a anotação manual será perdida).")

    from db.chroma import get_chroma_db

    with open(QUESTIONS_PATH, encoding="utf-8") as file:
        questions = json.load(file)

    retriever = get_chroma_db().as_retriever()
    rows, retrieval_times = [], {}
    for question in questions:
        started = time.perf_counter()
        documents = retriever.invoke(question["question"])
        retrieval_times[question["id"]] = time.perf_counter() - started

        for doc in documents:
            rows.append({
                "question_id": question["id"],
                "question_type": question["type"],
                "question": question["question"],
                "chunk_id": doc.id,
                "chunk_text": doc.page_content,
                "lang": detect_language(doc.page_content),
                "gold_label": "",
            })
        print(f"🤖 {question['id']}: {len(documents)} chunks em {retrieval_times[question['id']]:.3f}s")

    with open(DATASET_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=DATASET_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    with open(RETRIEVAL_TIMES_PATH, "w", encoding="utf-8") as file:
        json.dump(retrieval_times, file, indent=2)

    print(f"🤖 {len(rows)} pares pergunta-chunk gravados em {DATASET_PATH}. Preencha a coluna gold_label com: relevant, partially_relevant ou not_relevant")

if __name__ == "__main__":
    main()
