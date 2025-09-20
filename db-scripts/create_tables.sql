CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario VARCHAR(255) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP NULL
);

-- Índice para otimizar consultas por usuário
CREATE INDEX idx_usuarios_usuario ON usuarios(usuario);

CREATE TABLE question_and_answer(
    id SERIAL PRIMARY KEY,
    user_id uuid NOT NULL,
    question text NOT NULL,
    answer text NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_question_answer ON question_and_answer (user_id, question, answer);
ALTER TABLE question_and_answer ADD CONSTRAINT fk_user_question_answer__user FOREIGN KEY (user_id) REFERENCES usuarios(id);

CREATE TABLE evaluation(
    id SERIAL PRIMARY KEY,
    question_answer_id INTEGER NOT NULL,
    llm_evaluation_reasoning TEXT NOT NULL,
    llm_evaluation_score DECIMAL NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE evaluation ADD CONSTRAINT fk_evaluation__question_answer FOREIGN KEY (question_answer_id) REFERENCES question_and_answer(id);
