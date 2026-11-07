import fetchContextEvaluations from './fetchContextEvaluations';
import { apiResponse, mockFetchOnce } from '../testUtils';

beforeEach(() => {
    global.fetch = jest.fn();
    localStorage.setItem('authToken', 'token-de-teste');
});

test('envia a página e o token', async () => {
    mockFetchOnce(apiResponse([]));

    await fetchContextEvaluations(2, '');

    const [url, options] = global.fetch.mock.calls[0];
    expect(url).toBe('/acd/avaliacoes-contexto?page=2');
    expect(options.headers.Authorization).toBe('Bearer token-de-teste');
});

test('envia o avaliador quando informado', async () => {
    mockFetchOnce(apiResponse([]));

    await fetchContextEvaluations(1, 'jev');

    expect(global.fetch.mock.calls[0][0]).toBe('/acd/avaliacoes-contexto?page=1&evaluator=jev');
});

test('retorna os dados da API', async () => {
    const body = apiResponse([]);
    mockFetchOnce(body);

    await expect(fetchContextEvaluations(1)).resolves.toEqual(body);
});

test('usa a mensagem de erro da API', async () => {
    mockFetchOnce({ status: 'error', erro: 'Não tem as permissões necessárias' }, 403);

    await expect(fetchContextEvaluations(1)).rejects.toThrow('Não tem as permissões necessárias');
});

test('informa o status quando a resposta de erro não é JSON', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false, status: 502, json: async () => { throw new SyntaxError('html'); } });

    await expect(fetchContextEvaluations(1)).rejects.toThrow('Erro na requisição: 502');
});
