import csv

import pytest

from benchmark import metrics

R, P, N = "relevant", "partially_relevant", "not_relevant"
GOLD = [R, R, P, N, N, P]
PREDICTED = [R, P, P, N, R, N]

def test_accuracy():
    assert metrics.accuracy(GOLD, PREDICTED) == 0.5
    assert metrics.accuracy([], []) == 0.0

def test_per_class_metrics():
    per_class = metrics.per_class_metrics(GOLD, PREDICTED)

    for label in (R, P, N):
        assert per_class[label] == {"precision": 0.5, "recall": 0.5, "f1": 0.5, "support": 2}

def test_per_class_metrics_without_predictions_for_a_class():
    per_class = metrics.per_class_metrics([R, P], [R, R])

    assert per_class[P] == {"precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 1}
    assert per_class[R]["precision"] == 0.5
    assert per_class[R]["recall"] == 1.0

def test_macro_f1():
    assert metrics.macro_f1(GOLD, PREDICTED) == 0.5

def test_confusion_matrix():
    matrix = metrics.confusion_matrix(GOLD, PREDICTED)

    assert matrix[R] == {R: 1, P: 1, N: 0}
    assert matrix[P] == {R: 0, P: 1, N: 1}
    assert matrix[N] == {R: 1, P: 0, N: 1}

def test_cohen_kappa():
    assert metrics.cohen_kappa(GOLD, PREDICTED) == pytest.approx(0.25)
    assert metrics.cohen_kappa(GOLD, GOLD) == pytest.approx(1.0)
    assert metrics.cohen_kappa([R, R], [R, R]) == 1.0

def test_binary_collapses_partially_relevant_into_not_relevant():
    assert metrics.to_binary([R, P, N]) == [R, N, N]
    assert metrics.classification_report(GOLD, PREDICTED)["binary"]["accuracy"] == pytest.approx(4 / 6)

def test_percentile_uses_linear_interpolation():
    assert metrics.percentile([4, 1, 3, 2], 50) == 2.5
    assert metrics.percentile([1, 2, 3, 4], 95) == pytest.approx(3.85)
    assert metrics.percentile([7], 95) == 7
    assert metrics.percentile([], 50) == 0.0

def test_latency_summary():
    summary = metrics.latency_summary([1.0, 2.0, 3.0, 4.0])

    assert summary["mean"] == 2.5
    assert summary["total"] == 10.0
    assert summary["n"] == 4
    assert metrics.latency_summary([])["n"] == 0

def write_dataset(path, labels):
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["question_id", "question", "chunk_id", "chunk_text", "lang", "gold_label"])
        writer.writeheader()
        for i, label in enumerate(labels):
            writer.writerow({"question_id": "q1", "question": "?", "chunk_id": f"c{i}", "chunk_text": "t", "lang": "pt", "gold_label": label})

def test_load_annotated_dataset_normalizes_labels(tmp_path):
    path = tmp_path / "dataset.csv"
    write_dataset(path, [" Relevant ", "NOT_RELEVANT"])

    rows = metrics.load_annotated_dataset(path)

    assert [row["gold_label"] for row in rows] == [R, N]
    assert list(metrics.group_by_question(rows)) == ["q1"]

@pytest.mark.parametrize("label", ["", "irrelevante"])
def test_load_annotated_dataset_rejects_missing_or_invalid_labels(tmp_path, label):
    path = tmp_path / "dataset.csv"
    write_dataset(path, [R, label])

    with pytest.raises(ValueError, match="1 linha"):
        metrics.load_annotated_dataset(path)
