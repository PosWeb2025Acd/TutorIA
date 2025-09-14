CREATE TABLE evaluation(
    id SERIAL PRIMARY KEY,
    question_answer_id INTEGER NOT NULL,
    llm_evaluation_reasoning TEXT NOT NULL,
    llm_evaluation_score DECIMAL NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE evaluation ADD CONSTRAINT fk_evaluation__question_answer FOREIGN KEY (question_answer_id) REFERENCES question_and_answer(id);
