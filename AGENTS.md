# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Overview

TutorIA is a computer-science tutoring assistant (TCC project) built as a corrective RAG system on local LLMs served by Ollama. Code comments, API messages, DB column names, and UI text are mostly in Portuguese; keep new user-facing strings in Portuguese.

## Running

Everything runs through Docker Compose (Ollama service needs the NVIDIA Container Toolkit for GPU access). Copy `env.example` to `.env` and fill it in first.

```bash
./init.sh                    # FIRST RUN ONLY: compose up --build, pulls llama3.1:8b + deepseek-r1:8b into Ollama, sets up LangGraph checkpointer tables
docker compose up -d --build # subsequent runs
docker compose logs -f rag   # services: rag, judge, frontend, db, ollama
./drop_containers_and_db.sh  # compose down + delete Postgres volume (re-runs db-scripts/ on next start)
./kill.sh                    # same, but also deletes the Ollama models volume
```

After wiping the DB volume, re-run the checkpointer setup: `docker compose exec rag /app/scripts/init_checkpointer.sh`.

Frontend (`app/`, Create React App): `npm start`, `npm run build`, `npm test` (react-scripts/Jest; no tests exist yet). No linter is configured.

## Testing

**Project standard: every new feature or behavior change must ship with unit and integration tests.** Code that predates this rule (written before the JEV context evaluator) has no tests; covering it is optional, but anything you add or change must be covered.

The `rag` service uses pytest (`rag/pytest.ini`, `rag/requirements-dev.txt`, installed in the rag image):

```bash
docker compose exec rag python -m pytest          # unit + offline integration (default, also runs in CI)
docker compose exec rag python -m pytest -m live  # hits real Ollama + TypeSafe API; skipped without OLLAMA_URL / TYPESAFE_API_KEY
```

Outside the container, run `python -m pytest` from `rag/` (`pythonpath = . ..` makes the repo-root `db/` package importable).

- `rag/tests/unit/` tests one module in isolation; `rag/tests/integration/` exercises the compiled LangGraph or full scripts end to end with fakes. Tests that need real external services are marked `@pytest.mark.live` and excluded by default.
- Shared fakes live in `rag/tests/conftest.py`: `FakeLLM` (answers by graph step), `FakeJevApi` (real `TypeSafeClient` over an `httpx2.MockTransport`), `FakeVectorStore`, and a stub for `db.chroma` so importing `rag_graph` doesn't load Chroma or the embedding model. Default tests must not need network, Postgres, Ollama, or API keys.
- Keep new modules testable: no network clients or heavy resources created at import time (see the lazy `_get_jev_client()` in `rag/rag_graph/context_evaluators.py`).
- CI: `.github/workflows/rag-tests.yml` runs `pytest` on PRs and pushes to `main` that touch `rag/` or `db/`. If you add tests to another service, add a matching workflow.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how the services fit together, shared code and import rules, API conventions, the database schema, and the LLMs used. Read it before making changes that touch more than one service.
