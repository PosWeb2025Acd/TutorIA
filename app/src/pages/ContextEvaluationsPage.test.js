import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import ContextEvaluationsPage from './ContextEvaluationsPage';
import { JEV_EVALUATION, LLM_FALLBACK_EVALUATION, apiResponse, loginAs, mockFetchOnce } from '../testUtils';

const renderPage = () => render(<MemoryRouter><ContextEvaluationsPage /></MemoryRouter>);
const questionButton = (question) => screen.getByRole('button', { name: new RegExp(question) });
const lastUrl = () => global.fetch.mock.calls.at(-1)[0];

beforeEach(() => {
    global.fetch = jest.fn();
    loginAs({ usuario: 'admin', admin: true });
});

afterEach(() => localStorage.clear());

test('lista as perguntas identificando o avaliador, sem abrir o detalhe', async () => {
    mockFetchOnce(apiResponse([JEV_EVALUATION, LLM_FALLBACK_EVALUATION]));

    renderPage();

    const jev = await screen.findByRole('button', { name: /polimorfismo/ });
    expect(within(jev).getByText('JEV')).toBeInTheDocument();
    expect(within(jev).getByText('1 de 2 chunks usados')).toBeInTheDocument();
    const llm = questionButton('herança');
    expect(within(llm).getByText('LLM')).toBeInTheDocument();
    expect(within(llm).getByText('Fallback')).toBeInTheDocument();
    expect(within(llm).getByText('Nenhum de 1 chunks usado')).toBeInTheDocument();
    expect(screen.queryByText(JEV_EVALUATION.chunks[0].content)).not.toBeInTheDocument();
});

test('clicar na pergunta mostra o contexto e a avaliação, sem nova requisição', async () => {
    mockFetchOnce(apiResponse([JEV_EVALUATION, LLM_FALLBACK_EVALUATION]));
    renderPage();

    const button = await screen.findByRole('button', { name: /polimorfismo/ });
    await userEvent.click(button);

    expect(button).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText(JEV_EVALUATION.chunks[0].content)).toBeInTheDocument();
    expect(screen.getByText('Probabilidade: 94.0%')).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledTimes(1);
});

test('só uma pergunta fica aberta, e clicar de novo fecha', async () => {
    mockFetchOnce(apiResponse([JEV_EVALUATION, LLM_FALLBACK_EVALUATION]));
    renderPage();

    await userEvent.click(await screen.findByRole('button', { name: /polimorfismo/ }));
    await userEvent.click(questionButton('herança'));

    expect(screen.queryByText(JEV_EVALUATION.chunks[0].content)).not.toBeInTheDocument();
    expect(screen.getByText(LLM_FALLBACK_EVALUATION.chunks[0].content)).toBeInTheDocument();

    await userEvent.click(questionButton('herança'));
    expect(screen.queryByText(LLM_FALLBACK_EVALUATION.chunks[0].content)).not.toBeInTheDocument();
});

test('filtrar por avaliador consulta a API e volta para a primeira página', async () => {
    mockFetchOnce(apiResponse([JEV_EVALUATION], { total_pages: 3, total_evaluations: 25 }));
    renderPage();
    await userEvent.click(await screen.findByRole('button', { name: '2' }));
    await waitFor(() => expect(lastUrl()).toContain('page=2'));

    mockFetchOnce(apiResponse([JEV_EVALUATION]));
    await userEvent.click(within(screen.getByRole('group')).getByRole('button', { name: 'JEV' }));

    await waitFor(() => expect(lastUrl()).toBe('/acd/avaliacoes-contexto?page=1&evaluator=jev'));
    expect(within(screen.getByRole('group')).getByRole('button', { name: 'JEV' })).toHaveAttribute('aria-pressed', 'true');
});

test('mudar de página busca a página nova e fecha o detalhe', async () => {
    mockFetchOnce(apiResponse([JEV_EVALUATION], { total_pages: 2, total_evaluations: 11 }));
    renderPage();
    await userEvent.click(await screen.findByRole('button', { name: /polimorfismo/ }));

    mockFetchOnce(apiResponse([LLM_FALLBACK_EVALUATION], { total_pages: 2, total_evaluations: 11 }));
    await userEvent.click(screen.getByRole('button', { name: 'Próxima' }));

    await screen.findByRole('button', { name: /herança/ });
    expect(lastUrl()).toBe('/acd/avaliacoes-contexto?page=2');
    expect(screen.queryByText(JEV_EVALUATION.chunks[0].content)).not.toBeInTheDocument();
});

test('atualizar consulta a API de novo', async () => {
    mockFetchOnce(apiResponse([JEV_EVALUATION]));
    renderPage();
    await screen.findByRole('button', { name: /polimorfismo/ });

    mockFetchOnce(apiResponse([JEV_EVALUATION, LLM_FALLBACK_EVALUATION]));
    await userEvent.click(screen.getByRole('button', { name: 'Atualizar' }));

    await screen.findByRole('button', { name: /herança/ });
    expect(global.fetch).toHaveBeenCalledTimes(2);
});

test('mostra uma mensagem quando não há avaliações', async () => {
    mockFetchOnce(apiResponse([]));

    renderPage();

    expect(await screen.findByText('Nenhuma avaliação encontrada')).toBeInTheDocument();
});

test('mostra o erro da API', async () => {
    mockFetchOnce({ status: 'error', erro: 'Erro interno do servidor.' }, 500);

    renderPage();

    expect(await screen.findByText('Erro interno do servidor.')).toBeInTheDocument();
    expect(screen.queryByText('Nenhuma avaliação encontrada')).not.toBeInTheDocument();
});

test('uma resposta antiga não sobrescreve a consulta atual', async () => {
    let resolveOld;
    global.fetch.mockReturnValueOnce(new Promise((resolve) => { resolveOld = resolve; }));
    renderPage();

    mockFetchOnce(apiResponse([LLM_FALLBACK_EVALUATION]));
    await userEvent.click(within(screen.getByRole('group')).getByRole('button', { name: 'LLM' }));
    await screen.findByRole('button', { name: /herança/ });

    resolveOld({ ok: true, status: 200, json: async () => apiResponse([JEV_EVALUATION]) });
    await new Promise((resolve) => setTimeout(resolve));

    expect(screen.queryByRole('button', { name: /polimorfismo/ })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /herança/ })).toBeInTheDocument();
});
