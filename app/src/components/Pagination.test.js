import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Pagination from './Pagination';

const renderPagination = (currentPage, totalPages, onPageChange = jest.fn()) => {
    render(<Pagination currentPage={currentPage} totalPages={totalPages} shownCount={10} totalCount={95} onPageChange={onPageChange} />);
    return onPageChange;
};

const pageNumbers = () => screen.getAllByRole('button').map((button) => button.textContent).filter((text) => /^\d+$/.test(text)).map(Number);

test.each([
    [1, 3, [1, 2, 3]],
    [1, 10, [1, 2, 3, 4, 5]],
    [5, 10, [3, 4, 5, 6, 7]],
    [10, 10, [6, 7, 8, 9, 10]],
])('página %i de %i mostra a janela certa', (currentPage, totalPages, expected) => {
    renderPagination(currentPage, totalPages);

    expect(pageNumbers()).toEqual(expected);
});

test('mostra o resumo e marca a página atual', () => {
    renderPagination(2, 10);

    expect(screen.getByText(/Página 2 de 10/)).toBeInTheDocument();
    expect(screen.getByText(/10 de 95 registros/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '2' })).toHaveAttribute('aria-current', 'page');
});

test('navega pelos botões', async () => {
    const onPageChange = renderPagination(2, 10);

    await userEvent.click(screen.getByRole('button', { name: 'Próxima' }));
    await userEvent.click(screen.getByRole('button', { name: 'Anterior' }));
    await userEvent.click(screen.getByRole('button', { name: '4' }));

    expect(onPageChange.mock.calls).toEqual([[3], [1], [4]]);
});

test('desabilita os botões nos limites', () => {
    renderPagination(1, 1);

    expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Próxima' })).toBeDisabled();
});
