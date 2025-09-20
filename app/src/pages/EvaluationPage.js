import React, { useState, useEffect, useCallback } from 'react';
import {
    RefreshCw,
    ChevronLeft,
    ChevronRight,
    AlertCircle,
    Calendar,
    User,
    MessageSquare,
    FileText,
    Loader2,
    Star,
    BookOpen
} from 'lucide-react';
import Header from '../components/Header';
import handleLogout from '../functions/userLogout';
import checkToken from '../functions/checkToken';

const AnswerEvaluationsPage = () => {
    const [avaliacoes, setAvaliacoes] = useState([]);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalEvaluations, setTotalEvaluations] = useState(0);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [userData, setUserData] = useState(null);

    // Função para obter o token do localStorage
    const getAuthToken = () => {
        return localStorage.getItem('authToken');
    };

    // Função para fazer a requisição à API
    const fetchAvaliacoes = useCallback(async (page = 1) => {
        setIsLoading(true);
        setError(null);

        try {
            const token = getAuthToken();

            if (!token) {
                throw new Error('Token de autenticação não encontrado. Faça login novamente.');
            }

            const response = await fetch(`/acd/avaliacoes-resposta?page=${page}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Sessão expirada. Faça login novamente.');
                } else if (response.status === 403) {
                    throw new Error('Acesso negado.');
                } else {
                    throw new Error(`Erro na requisição: ${response.status}`);
                }
            }

            const data = await response.json();

            // Processa a nova estrutura da API
            if (data.evaluation_list && Array.isArray(data.evaluation_list)) {
                setAvaliacoes(data.evaluation_list);
                setTotalPages(data.total_pages || 1);
                setTotalEvaluations(data.total_evaluations || 0);
            } else {
                // Fallback para estrutura não esperada
                setAvaliacoes([]);
                setTotalPages(1);
                setTotalEvaluations(0);
            }

        } catch (err) {
            console.error('Erro ao carregar avaliações:', err);
            setError(err.message);
            setAvaliacoes([]);
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Carrega dados ao montar o componente
    useEffect(() => {
        try {
            const parsedUserData = checkToken();
            setUserData(parsedUserData);
        } catch(error) {
            localStorage.removeItem('authToken');
            localStorage.removeItem('userData');
            window.location.href = '/login';
        }
        
        fetchAvaliacoes(currentPage);
    }, [fetchAvaliacoes, currentPage]);

    // Função para atualizar os dados (refresh)
    const handleRefresh = () => {
        fetchAvaliacoes(currentPage);
    };

    // Função para navegar entre páginas
    const handlePageChange = (newPage) => {
        if (newPage >= 1 && newPage <= totalPages) {
            setCurrentPage(newPage);
        }
    };

    // Função para formatar data
    const formatDate = (dateString) => {
        try {
            // Se a data já está no formato brasileiro
            if (dateString && dateString.includes('/')) {
                return dateString;
            }
            // Caso contrário, tenta converter
            const date = new Date(dateString);
            return date.toLocaleString('pt-BR');
        } catch {
            return dateString || 'Data inválida';
        }
    };

    // Função para formatar e colorir o score
    const formatScore = (score) => {
        if (score === null || score === undefined) return 'N/A';

        const numScore = parseFloat(score);
        if (isNaN(numScore)) return score;

        // Define cor baseada na nota
        let colorClass = '';
        if (numScore >= 8) colorClass = 'text-green-600 bg-green-50';
        else if (numScore >= 6) colorClass = 'text-yellow-600 bg-yellow-50';
        else if (numScore >= 4) colorClass = 'text-orange-600 bg-orange-50';
        else colorClass = 'text-red-600 bg-red-50';

        return { score: numScore.toFixed(1), colorClass };
    };

    return (
        <div className="min-h-screen bg-gray-50 p-4">
            <Header userData={userData} onLogout={handleLogout} />

            <div className="max-w-7xl mx-auto mt-4">
                {/* Header */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
                    <div className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                                    <FileText className="h-6 w-6 text-blue-600" />
                                    Avaliações de Respostas
                                </h1>
                                <p className="text-gray-600 mt-1">
                                    Histórico de perguntas e respostas avaliadas pelo sistema TutorIA
                                </p>
                            </div>

                            <button
                                onClick={handleRefresh}
                                disabled={isLoading}
                                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                                Atualizar
                            </button>
                        </div>
                    </div>
                </div>

                {/* Mensagem de Erro */}
                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3">
                        <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                        <div>
                            <h3 className="font-medium text-red-800">Erro ao carregar dados</h3>
                            <p className="text-red-700 text-sm mt-1">{error}</p>
                        </div>
                    </div>
                )}

                {/* Tabela */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        <div className="flex items-center gap-2">
                                            <User className="h-4 w-4" />
                                            Usuário
                                        </div>
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        <div className="flex items-center gap-2">
                                            <MessageSquare className="h-4 w-4" />
                                            Pergunta
                                        </div>
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        <div className="flex items-center gap-2">
                                            <FileText className="h-4 w-4" />
                                            Resposta
                                        </div>
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        <div className="flex items-center gap-2">
                                            <Star className="h-4 w-4" />
                                            Avaliação
                                        </div>
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        <div className="flex items-center gap-2">
                                            <BookOpen className="h-4 w-4" />
                                            Justificativa
                                        </div>
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        <div className="flex items-center gap-2">
                                            <Calendar className="h-4 w-4" />
                                            Data da Avaliação
                                        </div>
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {isLoading ? (
                                    <tr>
                                        <td colSpan="6" className="px-6 py-12 text-center">
                                            <div className="flex items-center justify-center gap-2 text-gray-500">
                                                <Loader2 className="h-5 w-5 animate-spin" />
                                                Carregando avaliações...
                                            </div>
                                        </td>
                                    </tr>
                                ) : avaliacoes.length === 0 ? (
                                    <tr>
                                        <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                                            <div className="flex flex-col items-center gap-2">
                                                <FileText className="h-8 w-8 text-gray-300" />
                                                <p>Nenhuma avaliação encontrada</p>
                                                <p className="text-sm">Tente atualizar a página ou verificar outros períodos</p>
                                            </div>
                                        </td>
                                    </tr>
                                ) : (
                                    avaliacoes.map((avaliacao, index) => {
                                        const scoreData = formatScore(avaliacao.score);
                                        return (
                                            <tr key={index} className="hover:bg-gray-50 transition-colors">
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="text-sm font-medium text-gray-900">
                                                        {avaliacao.user || 'Usuário não informado'}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="text-sm text-gray-900 max-w-md">
                                                        <p className="line-clamp-2 leading-5">
                                                            {avaliacao.question || 'Pergunta não disponível'}
                                                        </p>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="text-sm text-gray-900 max-w-md">
                                                        <p className="line-clamp-3 leading-5">
                                                            {avaliacao.answer || 'Resposta não disponível'}
                                                        </p>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="flex items-center gap-1">
                                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${scoreData.colorClass}`}>
                                                            <Star className="h-3 w-3 mr-1" />
                                                            {scoreData.score}
                                                        </span>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="text-sm text-gray-900 max-w-xs">
                                                        <p className="line-clamp-2 leading-5">
                                                            {avaliacao.reasoning || 'Justificativa não disponível'}
                                                        </p>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="text-sm text-gray-900">
                                                        {formatDate(avaliacao.evaluation_date)}
                                                    </div>
                                                </td>
                                            </tr>
                                        );
                                    })
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* Paginação */}
                    {!isLoading && avaliacoes.length > 0 && (
                        <div className="bg-white px-6 py-3 border-t border-gray-200 flex items-center justify-between">
                            <div className="text-sm text-gray-500">
                                Página {currentPage} de {totalPages}
                                {avaliacoes.length > 0 && (
                                    <span> • {avaliacoes.length} de {totalEvaluations} registro{totalEvaluations !== 1 ? 's' : ''}</span>
                                )}
                            </div>

                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => handlePageChange(currentPage - 1)}
                                    disabled={currentPage <= 1}
                                    className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <ChevronLeft className="h-4 w-4" />
                                    Anterior
                                </button>

                                <div className="flex items-center gap-1">
                                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                        let pageNum;
                                        if (totalPages <= 5) {
                                            pageNum = i + 1;
                                        } else if (currentPage <= 3) {
                                            pageNum = i + 1;
                                        } else if (currentPage >= totalPages - 2) {
                                            pageNum = totalPages - 4 + i;
                                        } else {
                                            pageNum = currentPage - 2 + i;
                                        }

                                        return (
                                            <button
                                                key={pageNum}
                                                onClick={() => handlePageChange(pageNum)}
                                                className={`px-3 py-2 text-sm font-medium rounded-md ${currentPage === pageNum
                                                        ? 'bg-blue-600 text-white'
                                                        : 'text-gray-500 bg-white border border-gray-300 hover:bg-gray-50'
                                                    }`}
                                            >
                                                {pageNum}
                                            </button>
                                        );
                                    })}
                                </div>

                                <button
                                    onClick={() => handlePageChange(currentPage + 1)}
                                    disabled={currentPage >= totalPages}
                                    className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Próxima
                                    <ChevronRight className="h-4 w-4" />
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AnswerEvaluationsPage;