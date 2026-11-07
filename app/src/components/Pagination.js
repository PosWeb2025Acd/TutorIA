import { ChevronLeft, ChevronRight } from 'lucide-react';

const MAX_PAGE_BUTTONS = 5;

// Janela de até cinco páginas ao redor da página atual
const visiblePages = (currentPage, totalPages) => {
    const buttons = Math.min(MAX_PAGE_BUTTONS, totalPages);
    const lastStart = totalPages - buttons + 1;
    const start = Math.min(Math.max(currentPage - 2, 1), lastStart);

    return Array.from({ length: buttons }, (_, i) => start + i);
};

const Pagination = ({ currentPage, totalPages, shownCount, totalCount, onPageChange }) => {
    const goTo = (page) => {
        if (page >= 1 && page <= totalPages) {
            onPageChange(page);
        }
    };

    return (
        <div className="bg-white px-6 py-3 border-t border-gray-200 flex flex-wrap gap-2 items-center justify-between">
            <div className="text-sm text-gray-500">
                Página {currentPage} de {totalPages}
                <span> • {shownCount} de {totalCount} registro{totalCount !== 1 ? 's' : ''}</span>
            </div>

            <div className="flex items-center gap-2">
                <button
                    onClick={() => goTo(currentPage - 1)}
                    disabled={currentPage <= 1}
                    className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <ChevronLeft className="h-4 w-4" />
                    Anterior
                </button>

                <div className="flex items-center gap-1">
                    {visiblePages(currentPage, totalPages).map((page) => (
                        <button
                            key={page}
                            onClick={() => goTo(page)}
                            aria-current={currentPage === page ? 'page' : undefined}
                            className={`px-3 py-2 text-sm font-medium rounded-md ${currentPage === page
                                    ? 'bg-blue-600 text-white'
                                    : 'text-gray-500 bg-white border border-gray-300 hover:bg-gray-50'
                                }`}
                        >
                            {page}
                        </button>
                    ))}
                </div>

                <button
                    onClick={() => goTo(currentPage + 1)}
                    disabled={currentPage >= totalPages}
                    className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Próxima
                    <ChevronRight className="h-4 w-4" />
                </button>
            </div>
        </div>
    );
};

export default Pagination;
