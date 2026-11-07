export const JEV_EVALUATION = {
    id: 2,
    question: 'O que é polimorfismo?',
    answer: 'É a capacidade de objetos responderem à mesma mensagem.',
    user: 'aluno',
    evaluator: 'jev',
    config: { model: 'jev-1.13.0', min_probability: 0.7, criteria: { relevant: 'Responde diretamente' } },
    fallback_error: null,
    evaluation_date: '07/11/2026 15:33:33',
    chunks: [
        {
            position: 0,
            document_id: 'poo.pdf:3:1',
            content: 'Polimorfismo permite selecionar funcionalidades.',
            label: 'relevant',
            probability: 0.94,
            used: true,
            details: { probabilities: { not_relevant: 0.01, partially_relevant: 0.05, relevant: 0.94 }, score: 1.94, confidence: 0.8, model: 'jev-1.13.0' },
        },
        {
            position: 1,
            document_id: 'grafos.pdf:1:0',
            content: 'Um grafo é composto por vértices.',
            label: 'not_relevant',
            probability: 1,
            used: false,
            details: { probabilities: { not_relevant: 1, partially_relevant: 0, relevant: 0 }, score: 0.01, confidence: 0.9, model: 'jev-1.13.0' },
        },
    ],
};

export const LLM_FALLBACK_EVALUATION = {
    id: 1,
    question: 'O que é herança?',
    answer: 'Desculpe, mas não tenho informações suficientes.',
    user: 'outro-aluno',
    evaluator: 'llm',
    config: { model: 'llama3.1:8b', prompt: 'You are a grader' },
    fallback_error: 'POST https://api.typesafe.ai/v1/systemone: 401',
    evaluation_date: '07/11/2026 15:30:50',
    chunks: [
        { position: 0, document_id: 'poo.pdf:9:0', content: 'Classes organizam o código.', label: 'somewhat_relevant', probability: null, used: false, details: { raw_label: 'Somewhat_Relevant' } },
    ],
};

export const apiResponse = (evaluations, overrides = {}) => ({
    status: 'success',
    evaluation_list: evaluations,
    total_evaluations: evaluations.length,
    total_pages: evaluations.length ? 1 : 0,
    ...overrides,
});

export const mockFetchOnce = (body, status = 200) =>
    global.fetch.mockResolvedValueOnce({ ok: status < 400, status, json: async () => body });

export const loginAs = (user) => {
    localStorage.setItem('authToken', 'token-de-teste');
    localStorage.setItem('userData', JSON.stringify(user));
};
