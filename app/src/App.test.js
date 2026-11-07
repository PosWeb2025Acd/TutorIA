import { render, screen, waitFor } from '@testing-library/react';
import App from './App';
import { JEV_EVALUATION, apiResponse, loginAs } from './testUtils';

const CONTEXT_EVALUATIONS_PATH = '/tutor-ia/context-evaluations';
const contextRequests = () => global.fetch.mock.calls.filter(([url]) => url.startsWith('/acd/avaliacoes-contexto'));

beforeEach(() => {
    Element.prototype.scrollIntoView = jest.fn();
    global.fetch = jest.fn(async () => ({ ok: true, status: 200, json: async () => apiResponse([JEV_EVALUATION]) }));
    window.history.pushState({}, '', CONTEXT_EVALUATIONS_PATH);
});

afterEach(() => localStorage.clear());

test('o admin acessa a tela e vê o link no menu', async () => {
    loginAs({ usuario: 'admin', admin: true });

    render(<App />);

    expect(await screen.findByRole('heading', { name: 'Avaliações de Contexto' })).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: /polimorfismo/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Contexto' })).toHaveAttribute('href', CONTEXT_EVALUATIONS_PATH);
});

test('um aluno é redirecionado para o chat, sem link no menu e sem consultar a API', async () => {
    loginAs({ usuario: 'aluno', admin: false });

    render(<App />);

    await waitFor(() => expect(window.location.pathname).toBe('/tutor-ia/chat'));
    expect(screen.queryByRole('heading', { name: 'Avaliações de Contexto' })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Contexto' })).not.toBeInTheDocument();
    expect(contextRequests()).toEqual([]);
});

test('quem não fez login não vê a tela nem consulta a API', () => {
    // O logout redireciona com window.location, que o jsdom não implementa e reporta no console
    jest.spyOn(console, 'error').mockImplementation(() => {});

    render(<App />);

    expect(screen.queryByRole('heading', { name: 'Avaliações de Contexto' })).not.toBeInTheDocument();
    expect(contextRequests()).toEqual([]);
});
