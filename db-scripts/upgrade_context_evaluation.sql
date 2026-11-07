-- Registro das avaliações de contexto (LLM, JEV ou outro avaliador), para consulta posterior.
-- Idempotente: em um volume novo roda depois de create_tables.sql (ordem alfabética, necessária por causa da FK);
-- em um volume existente, aplique com o comando descrito em docs/ARCHITECTURE.md.

-- Uma linha por turno avaliado
CREATE TABLE IF NOT EXISTS context_evaluation(
    id SERIAL PRIMARY KEY,
    question_answer_id INTEGER NOT NULL REFERENCES question_and_answer(id),
    evaluator TEXT NOT NULL,
    config JSONB NOT NULL,
    fallback_error TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_context_evaluation_question_answer ON context_evaluation (question_answer_id);
CREATE INDEX IF NOT EXISTS idx_context_evaluation_evaluator_created_at ON context_evaluation (evaluator, created_at);

-- Uma linha por chunk recuperado, inclusive os descartados
CREATE TABLE IF NOT EXISTS context_evaluation_chunk(
    id SERIAL PRIMARY KEY,
    context_evaluation_id INTEGER NOT NULL REFERENCES context_evaluation(id),
    position INTEGER NOT NULL,
    document_id TEXT NOT NULL,
    content TEXT NOT NULL,
    label TEXT NOT NULL,
    probability DOUBLE PRECISION NULL,
    used BOOLEAN NOT NULL,
    details JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_context_evaluation_chunk_evaluation ON context_evaluation_chunk (context_evaluation_id);
