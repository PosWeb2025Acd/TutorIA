from benchmark.build_dataset import detect_language

def test_detects_portuguese():
    assert detect_language("O polimorfismo é um dos pilares da programação orientada a objetos e também da herança.") == "pt"

def test_detects_english():
    assert detect_language("Retrieval-augmented generation combines a retriever with the generator of a language model.") == "en"

def test_defaults_to_portuguese_without_evidence():
    assert detect_language("") == "pt"
