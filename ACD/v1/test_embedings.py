from sentence_transformers import SentenceTransformer

if __name__ == "__main__":

    # Load the model
    # model = SentenceTransformer("Qwen/Qwen3-Embedding-8B")

    # We recommend enabling flash_attention_2 for better acceleration and memory saving,
    # together with setting `padding_side` to "left":
    model = SentenceTransformer(
        "Qwen/Qwen3-Embedding-8B",
        model_kwargs={"attn_implementation": "flash_attention_2", "device_map": "auto"},
        tokenizer_kwargs={"padding_side": "left"},
    )

    # The queries and documents to embed
    queries = [
        "What is the capital of China?",
        "Explain gravity",
    ]
    documents = [
        "The capital of China is Beijing.",
        "Gravity is a force that attracts two bodies towards each other. It gives weight to physical objects and is responsible for the movement of planets around the sun.",
    ]

    # Encode the queries and documents. Note that queries benefit from using a prompt
    # Here we use the prompt called "query" stored under `model.prompts`, but you can
    # also pass your own prompt via the `prompt` argument
    query_embeddings = model.encode(queries, prompt_name="query")
    document_embeddings = model.encode(documents)
