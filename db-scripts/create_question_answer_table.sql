CREATE TABLE question_and_answer(
    id SERIAL PRIMARY KEY,
    user_id uuid NOT NULL,
    question text NOT NULL,
    answer text NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_question_answer ON question_and_answer (user_id, question, answer);
ALTER TABLE question_and_answer ADD CONSTRAINT fk_user_question_answer__user FOREIGN KEY (user_id) REFERENCES usuarios(id);