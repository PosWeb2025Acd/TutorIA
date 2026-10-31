"""
Compara os avaliadores de contexto (LLM local x JEV) sobre o dataset anotado manualmente.

Modos medidos, sempre sobre os mesmos chunks:
- llm: llama3.1:8b, um chunk por vez (comportamento atual do grafo)
- jev_sequential: JEV, uma requisição por vez
- jev_parallel: JEV, requisições em paralelo (JEV_MAX_WORKERS)

Uso (dentro do container rag): python -m benchmark.run_benchmark [--repetitions 3] [--modes llm jev_sequential jev_parallel]
"""

import argparse
import csv
import json
import os
import time

from datetime import datetime
from langchain_core.documents import Document

from benchmark import metrics
from benchmark.build_dataset import DATASET_PATH, RETRIEVAL_TIMES_PATH
from rag_graph.context_evaluators import EVALUATION_NOT_RELEVANT, EVALUATION_RELEVANT, JEV_MAX_WORKERS, grade_documents_jev, grade_documents_llm

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
MODES = ["llm", "jev_sequential", "jev_parallel"]
JEV_PRICE_PER_MTOK = 0.042
RELEVANT_THRESHOLDS = [0.3, 0.4, 0.5, 0.6, 0.7]

def grade_one_by_one(grader, question, documents):
    """
    Avalia cada chunk em uma chamada separada, medindo o tempo de cada uma.
    Uma falha (ex.: JSON inválido do LLM) é registrada e o chunk é tratado como not_relevant.
    """

    grades, times = [], []
    for doc in documents:
        started = time.perf_counter()
        try:
            grade = grader(question, [doc])[0]
        except Exception as e:
            grade = {"label": EVALUATION_NOT_RELEVANT, "error": f"{type(e).__name__}: {e}"}
        times.append(time.perf_counter() - started)
        grades.append(grade)

    return grades, times, sum(times)

def run_mode(mode, question, documents, jev_workers):
    if mode == "llm":
        return grade_one_by_one(grade_documents_llm, question, documents)
    if mode == "jev_sequential":
        return grade_one_by_one(lambda q, docs: grade_documents_jev(q, docs, max_workers=1), question, documents)

    started = time.perf_counter()
    try:
        grades = grade_documents_jev(question, documents, max_workers=jev_workers)
    except Exception as e:
        grades = [{"label": EVALUATION_NOT_RELEVANT, "error": f"{type(e).__name__}: {e}"} for _ in documents]
    elapsed = time.perf_counter() - started

    return grades, [elapsed / len(documents)] * len(documents), elapsed

def warm_up(modes, rows):
    """
    Primeira chamada carrega o modelo no Ollama / abre conexões HTTP; fica fora da medição.
    """

    doc = Document(id=rows[0]["chunk_id"], page_content=rows[0]["chunk_text"])
    if "llm" in modes:
        grade_one_by_one(grade_documents_llm, rows[0]["question"], [doc])
    if any(mode.startswith("jev") for mode in modes):
        grade_one_by_one(grade_documents_jev, rows[0]["question"], [doc])

def gate_report(questions, predictions):
    """
    Decisão do grafo por pergunta: responde se houver ao menos um chunk 'relevant'.
    """

    gold = [any(row["gold_label"] == EVALUATION_RELEVANT for row in rows) for rows in questions.values()]
    predicted = [any(predictions[row["chunk_id"], row["question_id"]] == EVALUATION_RELEVANT for row in rows) for rows in questions.values()]

    return {
        "accuracy": metrics.accuracy(gold, predicted),
        "answered_correctly": sum(g and p for g, p in zip(gold, predicted)),
        "refused_correctly": sum(not g and not p for g, p in zip(gold, predicted)),
        "answered_without_relevant_context": sum(not g and p for g, p in zip(gold, predicted)),
        "refused_with_relevant_context": sum(g and not p for g, p in zip(gold, predicted)),
    }

def threshold_report(rows, grades):
    """
    Decisão binária usando P(relevant) do JEV com limiares diferentes do argmax.
    """

    gold = metrics.to_binary([row["gold_label"] for row in rows])
    report = {}
    for threshold in RELEVANT_THRESHOLDS:
        predicted = [EVALUATION_RELEVANT if grade.get("probabilities", {}).get(EVALUATION_RELEVANT, 0.0) >= threshold else EVALUATION_NOT_RELEVANT for grade in grades]
        per_class = metrics.per_class_metrics(gold, predicted, [EVALUATION_RELEVANT, EVALUATION_NOT_RELEVANT])
        report[str(threshold)] = {"accuracy": metrics.accuracy(gold, predicted), "relevant": per_class[EVALUATION_RELEVANT]}

    return report

def summarize_mode(mode, rows, questions, runs, retrieval_times):
    """
    runs: uma lista por repetição com {"grades": [...], "chunk_times": [...], "question_times": {question_id: s}}.
    As métricas de assertividade usam a primeira repetição; a estabilidade compara os rótulos entre repetições.
    """

    first = runs[0]
    gold = [row["gold_label"] for row in rows]
    predicted = [grade["label"] for grade in first["grades"]]
    predictions = {(row["chunk_id"], row["question_id"]): label for row, label in zip(rows, predicted)}

    chunk_times = [t for run in runs for t in run["chunk_times"]]
    question_times = [t for run in runs for t in run["question_times"].values()]
    end_to_end = [retrieval_times[qid] + t for run in runs for qid, t in run["question_times"].items() if qid in retrieval_times]
    stable = sum(len({run["grades"][i]["label"] for run in runs}) == 1 for i in range(len(rows)))

    summary = {
        "mode": mode,
        "latency_per_chunk_s": metrics.latency_summary(chunk_times),
        "latency_per_question_s": metrics.latency_summary(question_times),
        "latency_retrieval_plus_evaluation_s": metrics.latency_summary(end_to_end),
        "classification": metrics.classification_report(gold, predicted),
        "by_language": {
            lang: metrics.classification_report([row["gold_label"] for row in rows if row["lang"] == lang], [p for row, p in zip(rows, predicted) if row["lang"] == lang])
            for lang in sorted({row["lang"] for row in rows})
        },
        "by_question_type": {
            qtype: metrics.classification_report([row["gold_label"] for row in rows if row["question_type"] == qtype], [p for row, p in zip(rows, predicted) if row["question_type"] == qtype])
            for qtype in sorted({row["question_type"] for row in rows})
        },
        "gate": gate_report(questions, predictions),
        "errors": sum("error" in grade for run in runs for grade in run["grades"]),
        "label_stability": stable / len(rows),
    }

    if mode.startswith("jev"):
        input_tokens = sum(grade.get("input_tokens", 0) for run in runs for grade in run["grades"])
        summary["jev"] = {
            "model": next((grade["model"] for grade in first["grades"] if "model" in grade), None),
            "input_tokens": input_tokens,
            "estimated_cost_usd": input_tokens * JEV_PRICE_PER_MTOK / 1_000_000,
            "mean_confidence": sum(grade.get("confidence", 0.0) for grade in first["grades"]) / len(rows),
            "thresholds": threshold_report(rows, first["grades"]),
        }

    return summary, predicted

def to_markdown(summaries, kappa_llm_jev):
    lines = [
        "| Modo | Latência/chunk média (s) | p95/chunk (s) | Latência/pergunta média (s) | Retrieval+avaliação média (s) | Acurácia | Macro-F1 | Acurácia binária | Acurácia do gate | Erros | Estabilidade |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in summaries.values():
        lines.append(
            f"| {s['mode']} | {s['latency_per_chunk_s']['mean']:.3f} | {s['latency_per_chunk_s']['p95']:.3f} | {s['latency_per_question_s']['mean']:.3f} | "
            f"{s['latency_retrieval_plus_evaluation_s']['mean']:.3f} | {s['classification']['accuracy']:.3f} | {s['classification']['macro_f1']:.3f} | "
            f"{s['classification']['binary']['accuracy']:.3f} | {s['gate']['accuracy']:.3f} | {s['errors']} | {s['label_stability']:.3f} |"
        )
    if kappa_llm_jev is not None:
        lines.append(f"\nConcordância LLM x JEV (Cohen's kappa): {kappa_llm_jev:.3f}")

    return "\n".join(lines) + "\n"

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", default=DATASET_PATH)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--modes", nargs="+", choices=MODES, default=MODES)
    parser.add_argument("--jev-workers", type=int, default=JEV_MAX_WORKERS)
    args = parser.parse_args()

    rows = metrics.load_annotated_dataset(args.dataset)
    questions = metrics.group_by_question(rows)
    retrieval_times = {}
    if os.path.exists(RETRIEVAL_TIMES_PATH):
        with open(RETRIEVAL_TIMES_PATH, encoding="utf-8") as file:
            retrieval_times = json.load(file)

    print(f"🤖 {len(rows)} chunks de {len(questions)} perguntas, modos {args.modes}, {args.repetitions} repetição(ões)")
    warm_up(args.modes, rows)

    runs = {mode: [] for mode in args.modes}
    for repetition in range(args.repetitions):
        for mode in args.modes:
            run = {"grades": [], "chunk_times": [], "question_times": {}}
            for question_id, question_rows in questions.items():
                documents = [Document(id=row["chunk_id"], page_content=row["chunk_text"]) for row in question_rows]
                grades, chunk_times, question_time = run_mode(mode, question_rows[0]["question"], documents, args.jev_workers)
                run["grades"].extend(grades)
                run["chunk_times"].extend(chunk_times)
                run["question_times"][question_id] = question_time
            runs[mode].append(run)
            print(f"🤖 repetição {repetition + 1}/{args.repetitions} - {mode}: {sum(run['question_times'].values()):.1f}s")

    # As linhas foram avaliadas na ordem de group_by_question; reordena para alinhar com as predições
    rows = [row for question_rows in questions.values() for row in question_rows]
    summaries, predictions = {}, {}
    for mode in args.modes:
        summaries[mode], predictions[mode] = summarize_mode(mode, rows, questions, runs[mode], retrieval_times)

    jev_mode = next((mode for mode in ("jev_parallel", "jev_sequential") if mode in predictions), None)
    kappa_llm_jev = metrics.cohen_kappa(predictions["llm"], predictions[jev_mode]) if "llm" in predictions and jev_mode else None

    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = {
        "created_at": timestamp,
        "dataset": {"chunks": len(rows), "questions": len(questions), "gold_distribution": {label: sum(row["gold_label"] == label for row in rows) for label in metrics.LABELS}},
        "repetitions": args.repetitions,
        "jev_workers": args.jev_workers,
        "kappa_llm_vs_jev": kappa_llm_jev,
        "modes": summaries,
    }
    with open(os.path.join(RESULTS_DIR, f"benchmark_{timestamp}.json"), "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)

    with open(os.path.join(RESULTS_DIR, f"benchmark_{timestamp}_predictions.csv"), "w", newline="", encoding="utf-8") as file:
        fields = ["question_id", "question_type", "chunk_id", "lang", "gold_label"] + [f"{mode}_label" for mode in args.modes] + [f"{mode}_p_relevant" for mode in args.modes if mode.startswith("jev")]
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for i, row in enumerate(rows):
            line = {field: row[field] for field in ("question_id", "question_type", "chunk_id", "lang", "gold_label")}
            for mode in args.modes:
                line[f"{mode}_label"] = predictions[mode][i]
                if mode.startswith("jev"):
                    line[f"{mode}_p_relevant"] = runs[mode][0]["grades"][i].get("probabilities", {}).get(EVALUATION_RELEVANT, "")
            writer.writerow(line)

    markdown = to_markdown(summaries, kappa_llm_jev)
    with open(os.path.join(RESULTS_DIR, f"benchmark_{timestamp}.md"), "w", encoding="utf-8") as file:
        file.write(markdown)

    print(markdown)
    print(f"🤖 Resultados gravados em {RESULTS_DIR}/benchmark_{timestamp}.*")

if __name__ == "__main__":
    main()
