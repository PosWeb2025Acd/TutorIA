import csv
import json
import sys
import types

import pytest

from benchmark import build_dataset, run_benchmark
from tests.conftest import FakeVectorStore, NOT_RELEVANT_TEXT, PARTIAL_TEXT, RELEVANT_TEXT, make_document

@pytest.fixture
def benchmark_paths(monkeypatch, tmp_path):
    questions = [
        {"id": "q1", "question": "O que é polimorfismo?", "type": "in_corpus"},
        {"id": "q2", "question": "Qual a melhor receita de bolo?", "type": "out_of_corpus"},
    ]
    (tmp_path / "questions.json").write_text(json.dumps(questions), encoding="utf-8")

    paths = {
        "questions": tmp_path / "questions.json",
        "dataset": tmp_path / "dataset.csv",
        "retrieval_times": tmp_path / "retrieval_times.json",
        "results": tmp_path / "results",
    }
    monkeypatch.setattr(build_dataset, "QUESTIONS_PATH", str(paths["questions"]))
    monkeypatch.setattr(build_dataset, "DATASET_PATH", str(paths["dataset"]))
    monkeypatch.setattr(build_dataset, "RETRIEVAL_TIMES_PATH", str(paths["retrieval_times"]))
    monkeypatch.setattr(run_benchmark, "RETRIEVAL_TIMES_PATH", str(paths["retrieval_times"]))
    monkeypatch.setattr(run_benchmark, "RESULTS_DIR", str(paths["results"]))

    documents = [
        make_document("poo.pdf:1:0", RELEVANT_TEXT),
        make_document("poo.pdf:2:0", PARTIAL_TEXT),
        make_document("grafos.pdf:1:0", NOT_RELEVANT_TEXT),
    ]
    monkeypatch.setitem(sys.modules, "db.chroma", types.SimpleNamespace(get_chroma_db=lambda: FakeVectorStore(documents)))
    return paths

def annotate(path, labels):
    with open(path, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    for row, label in zip(rows, labels):
        row["gold_label"] = label
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=build_dataset.DATASET_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

def test_build_dataset_writes_rows_for_annotation(monkeypatch, benchmark_paths):
    monkeypatch.setattr(sys, "argv", ["build_dataset"])

    build_dataset.main()

    with open(benchmark_paths["dataset"], newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 6
    assert {row["gold_label"] for row in rows} == {""}
    assert rows[0]["question_type"] == "in_corpus"
    assert set(json.loads(benchmark_paths["retrieval_times"].read_text())) == {"q1", "q2"}

def test_build_dataset_does_not_overwrite_annotations(monkeypatch, benchmark_paths):
    benchmark_paths["dataset"].write_text("anotado", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["build_dataset"])

    with pytest.raises(SystemExit):
        build_dataset.main()

    assert benchmark_paths["dataset"].read_text(encoding="utf-8") == "anotado"

def test_run_benchmark_compares_all_modes(monkeypatch, benchmark_paths, fake_llm, fake_jev):
    monkeypatch.setattr(sys, "argv", ["build_dataset"])
    build_dataset.main()
    # q1: gabarito igual ao que os fakes respondem; q2 (fora do corpus): tudo not_relevant
    annotate(benchmark_paths["dataset"], ["relevant", "partially_relevant", "not_relevant"] + ["not_relevant"] * 3)
    monkeypatch.setattr(sys, "argv", ["run_benchmark", "--dataset", str(benchmark_paths["dataset"]), "--repetitions", "2"])

    run_benchmark.main()

    result_file = next(benchmark_paths["results"].glob("benchmark_*[0-9].json"))
    result = json.loads(result_file.read_text(encoding="utf-8"))
    assert set(result["modes"]) == {"llm", "jev_sequential", "jev_parallel"}
    assert result["kappa_llm_vs_jev"] == pytest.approx(1.0)
    for summary in result["modes"].values():
        # Os fakes classificam q2 igual a q1, então erram 2 dos 6 chunks e respondem quando deveriam recusar
        assert summary["classification"]["accuracy"] == pytest.approx(4 / 6)
        assert summary["gate"]["answered_correctly"] == 1
        assert summary["gate"]["answered_without_relevant_context"] == 1
        assert summary["errors"] == 0
        assert summary["label_stability"] == 1.0
        assert summary["latency_per_question_s"]["n"] == 4
    assert result["modes"]["jev_parallel"]["jev"]["input_tokens"] == 2 * 6 * 100
    assert len(list(benchmark_paths["results"].glob("*_predictions.csv"))) == 1
    assert len(list(benchmark_paths["results"].glob("*.md"))) == 1
