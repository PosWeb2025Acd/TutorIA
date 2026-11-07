import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import AnswerEvaluationsPage from './EvaluationPage';
import { loginAs } from '../testUtils';

test('a paginação continua buscando a página escolhida', async () => {
    loginAs({ usuario: 'admin', admin: true });
    global.fetch = jest.fn(async () => ({
        ok: true,
        status: 200,
        json: async () => ({
            status: 'success',
            evaluation_list: [{ user: 'aluno', question: 'Pergunta', answer: 'Resposta', score: 8, reasoning: 'Motivo', evaluation_date: '07/11/2026' }],
            total_pages: 2,
            total_evaluations: 11,
        }),
    }));

    render(<MemoryRouter><AnswerEvaluationsPage /></MemoryRouter>);
    await userEvent.click(await screen.findByRole('button', { name: 'Próxima' }));

    await waitFor(() => expect(global.fetch.mock.calls.at(-1)[0]).toBe('/acd/avaliacoes-resposta?page=2'));
    localStorage.clear();
});
