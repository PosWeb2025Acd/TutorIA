import { render, screen, within } from '@testing-library/react';
import ContextEvaluationDetail from './ContextEvaluationDetail';
import { JEV_EVALUATION, LLM_FALLBACK_EVALUATION } from '../testUtils';

const chunkItems = () => screen.getAllByRole('listitem').filter((item) => item.parentElement.tagName === 'OL');

test('mostra a resposta e o texto de cada chunk', () => {
    render(<ContextEvaluationDetail evaluation={JEV_EVALUATION} />);

    expect(screen.getByText(JEV_EVALUATION.answer)).toBeInTheDocument();
    JEV_EVALUATION.chunks.forEach((chunk) => {
        expect(screen.getByText(chunk.content)).toBeInTheDocument();
        expect(screen.getByText(chunk.document_id)).toBeInTheDocument();
    });
});

test('mostra rótulo, probabilidade e uso de cada chunk do JEV', () => {
    render(<ContextEvaluationDetail evaluation={JEV_EVALUATION} />);

    const [used, discarded] = chunkItems();
    expect(within(used).getByText('Relevante')).toBeInTheDocument();
    expect(within(used).getByText('Probabilidade: 94.0%')).toBeInTheDocument();
    expect(within(used).getByText('Usado na resposta')).toBeInTheDocument();
    expect(within(discarded).getByText('Probabilidade: 100.0%')).toBeInTheDocument();
    expect(within(discarded).getByText('Não usado')).toBeInTheDocument();
});

test('mostra a probabilidade de cada nível do JEV e os demais campos', () => {
    render(<ContextEvaluationDetail evaluation={JEV_EVALUATION} />);

    const used = chunkItems()[0];
    expect(within(used).getByText('Parcialmente relevante:')).toHaveTextContent('5.0%');
    expect(within(used).getByText('score: 1.94')).toBeInTheDocument();
});

test('as probabilidades de cada nível aparecem da maior para a menor', () => {
    render(<ContextEvaluationDetail evaluation={JEV_EVALUATION} />);

    const levels = within(chunkItems()[0]).getAllByRole('listitem').slice(0, 3).map((item) => item.textContent);
    expect(levels).toEqual(['Relevante: 94.0%', 'Parcialmente relevante: 5.0%', 'Não relevante: 1.0%']);
});

test('o LLM aparece sem probabilidade e um rótulo inesperado aparece como veio', () => {
    render(<ContextEvaluationDetail evaluation={LLM_FALLBACK_EVALUATION} />);

    const [chunk] = chunkItems();
    expect(within(chunk).getByText('somewhat_relevant')).toBeInTheDocument();
    expect(within(chunk).getByText('Sem probabilidade')).toBeInTheDocument();
    expect(within(chunk).getByText('raw_label: Somewhat_Relevant')).toBeInTheDocument();
});

test('avisa quando o resultado veio de um fallback, com o erro', () => {
    render(<ContextEvaluationDetail evaluation={LLM_FALLBACK_EVALUATION} />);

    expect(screen.getByText(/avaliador de reserva/)).toBeInTheDocument();
    expect(screen.getByText(LLM_FALLBACK_EVALUATION.fallback_error)).toBeInTheDocument();
});

test('não mostra o aviso de fallback sem erro', () => {
    render(<ContextEvaluationDetail evaluation={JEV_EVALUATION} />);

    expect(screen.queryByText(/avaliador de reserva/)).not.toBeInTheDocument();
});

test('mostra a configuração usada, seja qual for o avaliador', () => {
    const { unmount } = render(<ContextEvaluationDetail evaluation={LLM_FALLBACK_EVALUATION} />);
    expect(screen.getByText('You are a grader')).toBeInTheDocument();
    unmount();

    render(<ContextEvaluationDetail evaluation={JEV_EVALUATION} />);
    expect(screen.getByText('0.7')).toBeInTheDocument();
    expect(screen.getByText(/Responde diretamente/)).toBeInTheDocument();
});
