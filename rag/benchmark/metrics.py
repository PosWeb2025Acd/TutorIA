"""
Métricas do comparativo entre avaliadores de contexto. Python puro, sem dependências, para ser testável de forma isolada.
"""

import csv
import math

LABELS = ["relevant", "partially_relevant", "not_relevant"]

def confusion_matrix(gold, predicted, labels=LABELS):
    """
    matrix[gold_label][predicted_label] = quantidade
    """

    matrix = {g: {p: 0 for p in labels} for g in labels}
    for g, p in zip(gold, predicted):
        matrix[g][p] += 1

    return matrix

def accuracy(gold, predicted):
    if not gold:
        return 0.0

    return sum(g == p for g, p in zip(gold, predicted)) / len(gold)

def per_class_metrics(gold, predicted, labels=LABELS):
    metrics = {}
    for label in labels:
        tp = sum(g == label and p == label for g, p in zip(gold, predicted))
        fp = sum(g != label and p == label for g, p in zip(gold, predicted))
        fn = sum(g == label and p != label for g, p in zip(gold, predicted))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        metrics[label] = {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn}

    return metrics

def macro_f1(gold, predicted, labels=LABELS):
    metrics = per_class_metrics(gold, predicted, labels)
    return sum(m["f1"] for m in metrics.values()) / len(labels)

def cohen_kappa(a, b, labels=LABELS):
    """
    Concordância entre dois anotadores descontando a concordância esperada ao acaso.
    """

    n = len(a)
    if n == 0:
        return 0.0

    observed = sum(x == y for x, y in zip(a, b)) / n
    expected = sum((a.count(label) / n) * (b.count(label) / n) for label in labels)
    if expected == 1:
        return 1.0

    return (observed - expected) / (1 - expected)

def to_binary(labels):
    """
    Colapsa para a decisão usada pelo grafo: o chunk é 'relevant' ou não.
    """

    return ["relevant" if label == "relevant" else "not_relevant" for label in labels]

def percentile(values, q):
    """
    Percentil com interpolação linear (mesmo método padrão do numpy).
    """

    if not values:
        return 0.0

    ordered = sorted(values)
    position = (len(ordered) - 1) * q / 100
    lower, upper = math.floor(position), math.ceil(position)

    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)

def latency_summary(values):
    if not values:
        return {"mean": 0.0, "p50": 0.0, "p95": 0.0, "min": 0.0, "max": 0.0, "total": 0.0, "n": 0}

    return {
        "mean": sum(values) / len(values),
        "p50": percentile(values, 50),
        "p95": percentile(values, 95),
        "min": min(values),
        "max": max(values),
        "total": sum(values),
        "n": len(values),
    }

def classification_report(gold, predicted):
    return {
        "accuracy": accuracy(gold, predicted),
        "macro_f1": macro_f1(gold, predicted),
        "kappa_vs_gold": cohen_kappa(gold, predicted),
        "per_class": per_class_metrics(gold, predicted),
        "confusion_matrix": confusion_matrix(gold, predicted),
        "binary": {
            "accuracy": accuracy(to_binary(gold), to_binary(predicted)),
            "per_class": per_class_metrics(to_binary(gold), to_binary(predicted), ["relevant", "not_relevant"]),
        },
    }

def load_annotated_dataset(path):
    """
    Lê o CSV anotado. Todas as linhas precisam de um gold_label válido.
    """

    with open(path, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    invalid = [row["chunk_id"] for row in rows if row.get("gold_label", "").strip().lower() not in LABELS]
    if invalid:
        raise ValueError(f"{len(invalid)} linha(s) sem gold_label válido ({', '.join(LABELS)}). Ex.: {invalid[:5]}")

    for row in rows:
        row["gold_label"] = row["gold_label"].strip().lower()

    return rows

def group_by_question(rows):
    questions = {}
    for row in rows:
        questions.setdefault(row["question_id"], []).append(row)

    return questions
