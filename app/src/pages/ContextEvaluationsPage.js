import { useEffect, useState } from 'react';
import { AlertCircle, ChevronDown, ChevronRight, FileSearch, Loader2, RefreshCw } from 'lucide-react';
import ContextEvaluationDetail from '../components/ContextEvaluationDetail';
import EvaluatorBadge from '../components/EvaluatorBadge';
import Header from '../components/Header';
import Pagination from '../components/Pagination';
import checkToken from '../functions/checkToken';
import fetchContextEvaluations from '../functions/fetchContextEvaluations';
import handleLogout from '../functions/userLogout';

const EVALUATOR_FILTERS = [
    { value: '', text: 'Todos' },
    { value: 'jev', text: 'JEV' },
    { value: 'llm', text: 'LLM' },
];

const usedChunksSummary = (chunks) => {
    const used = chunks.filter((chunk) => chunk.used).length;

    return used === 0 ? `Nenhum de ${chunks.length} chunks usado` : `${used} de ${chunks.length} chunks usados`;
};

const ContextEvaluationsPage = () => {
    const [userData] = useState(() => checkToken());
    const [page, setPage] = useState(1);
    const [evaluator, setEvaluator] = useState('');
    const [reloadCount, setReloadCount] = useState(0);
    const [result, setResult] = useState({ evaluation_list: [], total_evaluations: 0, total_pages: 0 });
    const [openId, setOpenId] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        // Evita que a resposta de uma consulta antiga sobrescreva a da consulta atual
        let isCurrent = true;
        setIsLoading(true);
        setError(null);
        setOpenId(null);

        fetchContextEvaluations(page, evaluator)
            .then((data) => {
                if (isCurrent) setResult(data);
            })
            .catch((err) => {
                if (isCurrent) {
                    setError(err.message);
                    setResult({ evaluation_list: [], total_evaluations: 0, total_pages: 0 });
                }
            })
            .finally(() => {
                if (isCurrent) setIsLoading(false);
            });

        return () => {
            isCurrent = false;
        };
    }, [page, evaluator, reloadCount]);

    const changeEvaluator = (value) => {
        setEvaluator(value);
        setPage(1);
    };

    const evaluations = result.evaluation_list;

    return (
        <div className="min-h-screen bg-gray-50 p-4">
            <Header userData={userData} onLogout={handleLogout} />

            <div className="max-w-7xl mx-auto mt-4">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6 p-6">
                    <div className="flex flex-wrap gap-4 items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                                <FileSearch className="h-6 w-6 text-blue-600" />
                                Avaliações de Contexto
                            </h1>
                            <p className="text-gray-600 mt-1">
                                O que cada avaliador decidiu sobre os trechos recuperados para cada pergunta
                            </p>
                        </div>

                        <div className="flex flex-wrap items-center gap-3">
                            <div role="group" aria-label="Filtrar por avaliador" className="flex items-center gap-1">
                                {EVALUATOR_FILTERS.map(({ value, text }) => (
                                    <button
                                        key={text}
                                        onClick={() => changeEvaluator(value)}
                                        aria-pressed={evaluator === value}
                                        className={`px-3 py-2 text-sm font-medium rounded-md ${evaluator === value
                                                ? 'bg-blue-600 text-white'
                                                : 'text-gray-500 bg-white border border-gray-300 hover:bg-gray-50'
                                            }`}
                                    >
                                        {text}
                                    </button>
                                ))}
                            </div>

                            <button
                                onClick={() => setReloadCount((count) => count + 1)}
                                disabled={isLoading}
                                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                                Atualizar
                            </button>
                        </div>
                    </div>
                </div>

                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3">
                        <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                        <div>
                            <h3 className="font-medium text-red-800">Erro ao carregar dados</h3>
                            <p className="text-red-700 text-sm mt-1">{error}</p>
                        </div>
                    </div>
                )}

                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                    {isLoading ? (
                        <div className="px-6 py-12 flex items-center justify-center gap-2 text-gray-500">
                            <Loader2 className="h-5 w-5 animate-spin" />
                            Carregando avaliações...
                        </div>
                    ) : evaluations.length === 0 ? (
                        !error && <p className="px-6 py-12 text-center text-gray-500">Nenhuma avaliação encontrada</p>
                    ) : (
                        <>
                            <ul className="divide-y divide-gray-200">
                                {evaluations.map((evaluation) => {
                                    const isOpen = openId === evaluation.id;

                                    return (
                                        <li key={evaluation.id}>
                                            <button
                                                onClick={() => setOpenId(isOpen ? null : evaluation.id)}
                                                aria-expanded={isOpen}
                                                className="w-full px-6 py-4 text-left hover:bg-gray-50 transition-colors flex items-start gap-3"
                                            >
                                                {isOpen
                                                    ? <ChevronDown className="h-5 w-5 text-gray-400 flex-shrink-0 mt-0.5" />
                                                    : <ChevronRight className="h-5 w-5 text-gray-400 flex-shrink-0 mt-0.5" />}
                                                <span className="flex-1 min-w-0">
                                                    <span className="block text-sm font-medium text-gray-900 break-words">{evaluation.question}</span>
                                                    <span className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500">
                                                        <EvaluatorBadge evaluator={evaluation.evaluator} />
                                                        {evaluation.fallback_error && <span className="font-medium text-yellow-700">Fallback</span>}
                                                        <span>{usedChunksSummary(evaluation.chunks)}</span>
                                                        <span>{evaluation.user}</span>
                                                        <span>{evaluation.evaluation_date}</span>
                                                    </span>
                                                </span>
                                            </button>
                                            {isOpen && <ContextEvaluationDetail evaluation={evaluation} />}
                                        </li>
                                    );
                                })}
                            </ul>
                            <Pagination
                                currentPage={page}
                                totalPages={result.total_pages}
                                shownCount={evaluations.length}
                                totalCount={result.total_evaluations}
                                onPageChange={setPage}
                            />
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ContextEvaluationsPage;
