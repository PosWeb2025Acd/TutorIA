# Architecture

TutorIA answers computer-science questions using facts extracted from PDFs. Four independent processes share one Postgres database and one on-disk Chroma vector store; all LLM calls go to a local Ollama server.

```mermaid
flowchart LR
    user([Student / Admin]) --> app["app/ (React, :3000)"]
    app -- "CRA proxy /login, /acd/*" --> rag["rag/ (Flask + LangGraph, :5000)"]

    pdfs[/"process_files/documents/*.pdf"/] --> pf["process_files/ (ingestion loop)"]
    pf -- "embeddings + chunks" --> chroma[("Chroma<br/>db/tutor_ia_acd_db<br/>collection acd_collection")]

    rag -- "similarity search" --> chroma
    rag -- "users, checkpoints,<br/>question_and_answer" --> pg[("Postgres")]
    rag -- "llama3.1:8b" --> ollama["Ollama (:11434)"]

    judge["judge/ (evaluation loop)"] -- "unjudged Q&A / evaluation" --> pg
    judge -- "deepseek-r1:8b" --> ollama
```

| Process | Entry point | Runs as | Talks to |
|---|---|---|---|
| `rag` | `rag/main.py` | compose service, Flask on 5000 | Postgres, Chroma (read), Ollama |
| `judge` | `judge/main.py` | compose service, 15s loop | Postgres, Ollama |
| `process_files` | `process_files/process_files.py` | **manual**, 15s loop (not in compose) | Chroma (write) |
| `app` | `app/src/App.js` | compose service, CRA dev server on 3000 | `rag` via proxy `http://rag-tutoria:5000` |

The facts the tutor answers from only enter the system through `process_files`. The `POST /acd/enviar-arquivos` endpoint accepts a file but discards it, so it doesn't feed ingestion.

## 1. Ingestion: how facts reach the vector store

`process_files` turns PDFs into embedded chunks that the RAG step later retrieves. Run it from inside `process_files/`, because it resolves `documents/` and `processed_files.json` from `os.getcwd()`. It writes to `../db/tutor_ia_acd_db`, the same directory `rag` mounts at `/app/db`.

```mermaid
flowchart TD
    start([every 15s]) --> list["List process_files/documents/<br/>skip .gitkeep and names in processed_files.json"]
    list --> any{new files?}
    any -- no --> sleep([sleep 15s]) --> start
    any -- yes --> load["PyPDFLoader: one Document per page<br/>metadata: source, page"]
    load --> split["RecursiveCharacterTextSplitter<br/>chunk_size=1000, overlap=200"]
    split --> ids["Assign chunk id<br/>file_name:page:chunk_index"]
    ids --> dedupe["Chroma.get_by_ids → keep only ids not stored yet"]
    dedupe --> embed["HuggingFaceEmbeddings<br/>all-mpnet-base-v2 (768 dims)"]
    embed --> store[("Chroma acd_collection<br/>id = chunk id")]
    store --> mark["Append file names to processed_files.json"]
    mark --> sleep
```

- The chunk id (`poo.pdf:3:1`) is the citation shown to the user: RAG returns these ids as `sources`.
- A file is tracked by **name only**. If you replace a PDF with a new version under the same name, it isn't reprocessed until you remove the name from `processed_files.json` (and delete its chunks if their content changed).
- `process_files/chroma.py` duplicates `db/chroma.py`. The embedding model and collection name must stay the same in both, or the query embeddings won't match the stored ones.

## 2. Chat request, end to end

The chat page sends the question to `POST /acd/resposta`. Everything from authentication to the stored Q&A happens within that one request.

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser (ChatPage.js)
    participant F as Flask rag/main.py
    participant A as token_required_as_param
    participant PG as Postgres
    participant G as LangGraph (rag_graph.py)
    participant C as Chroma
    participant O as Ollama llama3.1:8b

    B->>F: POST /acd/resposta {question}<br/>Authorization: Bearer JWT
    F->>A: decorator
    A->>A: decode JWT (JWT_SECRET_KEY, HS256)
    A->>PG: get_user_by_id_and_user(user_id, user)
    PG-->>A: user row (or 403)
    A->>F: payload {user_id, user, admin, user_session_id}
    F->>PG: PostgresSaver.from_conn_string (checkpointer)
    F->>G: create_graph(checkpointer)<br/>invoke(messages=[question],<br/>thread_id=user_session_id, user_id)
    G->>PG: load checkpoint for thread_id (previous turns)
    G->>O: router prompt → {"choice": "vectorstore" | "llm"}
    alt vectorstore
        G->>C: retriever.invoke(question) (top 4 by similarity)
        C-->>G: 4 chunks (Document with id + page_content)
        loop each chunk
            G->>O: relevance grader → relevant / partially_relevant / not_relevant
        end
        G->>G: filter_graded_documents
    end
    alt has a relevant chunk
        G->>O: answer prompt (context + conversation)
        O-->>G: answer
    else none relevant
        G->>G: canned "não tenho informações suficientes"
    end
    G->>PG: INSERT question_and_answer (user_id, question, answer)
    G->>PG: save checkpoint (messages, documents, sources, flags)
    G-->>F: final state
    F-->>B: {status, answer, sources: [chunk ids]}
    B->>B: render answer + sources, save to localStorage
```

### Conversation memory

- Each login issues a JWT with a fresh `user_session_id` (UUID). That value becomes the LangGraph `thread_id`, so **one login = one conversation thread**. Logging out and back in starts a new history.
- The `PostgresSaver` checkpointer stores the full `RagState` for the thread after every step. Earlier turns' messages are passed to the answer prompt, which is how follow-up questions work.
- The browser's `localStorage` copy of messages is for display only. The server never reads it.
- The checkpointer tables are created once by `rag/scripts/checkpoint_setup.py`, which `init.sh` runs via `init_checkpointer.sh`.

## 3. The RAG graph

The graph is built in `create_graph()` (`rag/rag_graph/rag_graph.py`) and rebuilt on every request. Its state is `RagState`, a `MessagesState` extended with `documents`, `sources`, `has_relevant_documents`, `hallucination_grade` and `answer_grade`.

```mermaid
flowchart TD
    q([user question]) --> router{"__router_choice__<br/>LLM: computer science?"}
    router -- vectorstore --> retrieve["retrieve_context<br/>Chroma top-4 similarity"]
    router -- llm --> generate
    retrieve --> evaluate["retrieved_context_evaluator<br/>grade each chunk"]
    evaluate --> filter["filter_graded_documents<br/>keep relevant + partially_relevant<br/>has_relevant_documents = any relevant"]
    filter --> generate{"generate_answer<br/>has_relevant_documents?"}
    generate -- false --> refuse["canned refusal, sources = []"]
    generate -- true --> answer["LLM answer from context + history"]
    refuse --> save["save_question_and_answer<br/>INSERT question_and_answer"]
    answer --> save
    save --> e([END])
```

### Step by step

1. **Routing** (`__router_choice__`): llama3.1 classifies the question and returns JSON `{"choice": "vectorstore" | "llm"}`. Computer science, programming and technology questions go to the vector store.
2. **Retrieval** (`__retrieve_context__`): `vector_store.as_retriever()` uses LangChain's default plain similarity search with `k=4`. Chroma embeds the question with the same `all-mpnet-base-v2` model and returns the 4 closest chunks. `sources` is set to their chunk ids.
3. **Context evaluation** (`__retrieved_context_evaluator_llm__`, default): `grade_documents_llm` makes **one LLM call per chunk**, asking whether the chunk is `relevant`, `partially_relevant` or `not_relevant` to the question. This is a lenient keyword-style check meant to drop wrong retrievals.
   (The alternative JEV evaluator is selected with `CONTEXT_EVALUATOR=jev` and is out of scope here; see [JEV_CONTEXT_EVALUATOR.md](JEV_CONTEXT_EVALUATOR.md).)
4. **Filtering** (`filter_graded_documents`): keeps `relevant` chunks followed by `partially_relevant` ones and discards the rest. `sources` is narrowed to the kept ids. `has_relevant_documents` is true only if **at least one chunk is fully relevant**: partially relevant chunks are used as extra context but can't unlock an answer on their own.
5. **Answer** (`__generate_answer__`):
   - If there's no relevant chunk, it returns the canned Portuguese refusal with no sources.
   - Otherwise it builds a system prompt that limits the model to computer science and to **only the retrieved context** (at most ten sentences). The kept chunks are joined in reverse order (partially relevant first, relevant last, closest to the question). The thread's human/system/AI messages are appended, and llama3.1 produces the answer.
6. **Persistence** (`__save_question_and_answer__`): inserts the last question and answer, with `user_id` taken from the run config metadata, into `question_and_answer`. Every answer is saved, including refusals, and becomes input for the judge.

`__evaluate_answer_backed_by_context__`, a hallucination grader scoring 0–10 how well the chunks support the answer, is defined but **not wired into the graph**.

### Caveats in the current flow

These follow from reading the code. Check them before relying on them:

- The router calls the LLM **twice** and routes on the second result, which isn't lowercased. Any value other than exactly `vectorstore` / `llm` makes the graph fail.
- The `llm` route skips retrieval but still goes through `generate_answer`, which reads `has_relevant_documents` and uses the "only use the retrieved context" prompt. On a new thread that key hasn't been set yet, which should raise a `KeyError`. On an existing thread it reuses the **previous turn's** documents and flag. In practice the route only gives a sensible answer for off-topic questions when an earlier turn left relevant documents behind.
- `sources` contains chunk ids only (`file:page:chunk`, with `page` 0-based from `PyPDFLoader`), not page text.

## 4. The judge: LLM-as-a-judge, end to end

The judge scores every stored answer offline so admins can monitor answer quality. It runs separately from `rag`, so a slow judge never delays the chat.

```mermaid
sequenceDiagram
    autonumber
    participant J as judge/main.py loop
    participant PG as Postgres
    participant O as Ollama deepseek-r1:8b
    participant F as Flask rag/main.py
    participant B as Browser (EvaluationPage.js)

    loop every 15s
        J->>PG: SELECT id, question, answer FROM question_and_answer<br/>WHERE id NOT IN (SELECT question_answer_id FROM evaluation)<br/>ORDER BY created_at LIMIT 10
        PG-->>J: up to 10 unjudged pairs (or none)
        loop each pair
            J->>O: "is this answer useful to resolve the question?"<br/>→ JSON {score 0–10, reasoning}
            O-->>J: {score, reasoning}
            J->>PG: INSERT evaluation (question_answer_id, reasoning, score)
        end
        J->>J: close connection, sleep 15s
    end

    B->>F: GET /acd/avaliacoes-resposta?page=N (Bearer JWT)
    F->>F: token_required_as_param + admin_validate (403 if not admin)
    F->>PG: evaluation ⋈ question_and_answer ⋈ usuarios<br/>ORDER BY created_at DESC LIMIT 10 OFFSET (N-1)*10
    PG-->>F: rows + COUNT(*)
    F-->>B: {evaluation_list, total_evaluations, total_pages}
```

- **What it grades:** usefulness of the answer to the question, using **only the question and answer**. The judge never sees the retrieved chunks, so it measures helpfulness, not whether the answer is grounded in the PDFs.
- **Model:** `deepseek-r1:8b` at temperature 0 (`judge/judgement/llm.py`), deliberately a different model family from the one that generated the answer.
- **Queue semantics:** "unjudged" means "has no row in `evaluation`". The oldest pairs go first, 10 per round. Canned refusals are judged too.
- **Failure behavior:** `main.py` has no error handling around the LLM call or the JSON parse. One bad response crashes the process, compose `restart: always` restarts it, and it picks up the same oldest pair again.

## Shared code and imports

- The repo-root `db/` package (`postgres.py`, `chroma.py`) is shared by `rag` and `judge` via the compose volume mount `./db:/app/db`. Both services import it as `db.postgres` / `db.chroma` with `/app` as the working dir. The Chroma store itself is persisted under `db/tutor_ia_acd_db/` (gitignored).
- `rag/rag_graph/rag_graph.py` calls `get_chroma_db()` at import time, which loads the embedding model. Tests stub `db.chroma` for that reason (see `rag/tests/conftest.py`).
- Python modules inside each service use imports relative to the service root (e.g. `from api.token import ...`), so run them from that directory (or inside the container), not from repo root. The root-level `main.py` is a CLI REPL for the RAG graph and imports `rag.rag_graph...`, which conflicts with that convention.
- `rag` and `judge` read env vars (`DB_*`, `OLLAMA_URL`, `JWT_*`, `CONTEXT_EVALUATOR`) from `.env` via compose `env_file`.

## API conventions (rag)

- Auth: `@token_required_as_param` validates `Authorization: Bearer <jwt>`, checks the user still exists, and passes the decoded payload as the first positional arg to the view. Stack `@admin_validate` beneath it for admin-only endpoints.
- Responses are built manually with `Response(json.dumps(...), mimetype="application/json")` and carry a `status: "success"|"error"` field, with error text under `erro`.
- Controllers return `(success: bool, data, message)` tuples; repositories take a psycopg connection (rows as dicts via `dict_row`).

## Database

Schema lives in `db-scripts/create_tables.sql`, executed by the Postgres image only when the data volume is first created (no migration tool). The LangGraph checkpoint/store tables are created separately by `rag/scripts/checkpoint_setup.py`.

```mermaid
erDiagram
    usuarios ||--o{ question_and_answer : asks
    question_and_answer ||--o{ evaluation : "judged by (one per pair in practice)"
    usuarios {
        uuid id PK
        varchar usuario UK
        varchar senha "werkzeug hash"
        boolean is_admin
        timestamp data_criacao
    }
    question_and_answer {
        serial id PK
        uuid user_id FK
        text question
        text answer
        timestamp created_at
    }
    evaluation {
        serial id PK
        int question_answer_id FK
        text llm_evaluation_reasoning
        decimal llm_evaluation_score
        timestamp created_at
    }
```

## Models

LLM names are hard-coded constants: `MODEL = "llama3.1:8b"` in `rag/rag_graph/models.py`, `MODEL="deepseek-r1:8b"` in `judge/judgement/llm.py`. If you change one, update `init.sh` so the model gets pulled. All LLM steps expect JSON output parsed with `JsonOutputParser`. The embedding model `sentence-transformers/all-mpnet-base-v2` is set in both `db/chroma.py` and `process_files/chroma.py`. The optional JEV evaluator is an external API (`TYPESAFE_API_KEY`), pinned via `JEV_MODEL` (default `jev-1.13.0`) rather than the moving `jev-latest` alias.
