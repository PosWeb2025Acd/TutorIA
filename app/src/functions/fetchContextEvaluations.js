async function fetchContextEvaluations(page, evaluator) {
    const params = new URLSearchParams({ page });
    if (evaluator) {
        params.set('evaluator', evaluator);
    }

    const response = await fetch(`/acd/avaliacoes-contexto?${params}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.status !== 'success') {
        throw new Error(data.erro || `Erro na requisição: ${response.status}`);
    }

    return data;
}

export default fetchContextEvaluations;
