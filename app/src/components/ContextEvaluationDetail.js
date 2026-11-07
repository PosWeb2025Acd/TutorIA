import { AlertTriangle } from 'lucide-react';

const LABELS = {
    relevant: { text: 'Relevante', color: 'bg-green-100 text-green-800' },
    partially_relevant: { text: 'Parcialmente relevante', color: 'bg-yellow-100 text-yellow-800' },
    not_relevant: { text: 'Não relevante', color: 'bg-red-100 text-red-800' },
};

// Um rótulo fora dos esperados (ex.: o LLM não seguiu o prompt) aparece como veio, para ficar visível
const labelOf = (label) => LABELS[label] || { text: label, color: 'bg-gray-100 text-gray-800' };

const formatProbability = (probability) => `${(probability * 100).toFixed(1)}%`;

const ConfigValue = ({ value }) => (
    <dd className="text-sm text-gray-800 whitespace-pre-wrap break-words">
        {typeof value === 'object' && value !== null ? JSON.stringify(value, null, 2) : String(value)}
    </dd>
);

// Campos específicos de cada avaliador são exibidos como vieram, sem que a tela precise conhecê-los
const ChunkDetails = ({ details }) => {
    const { probabilities, ...others } = details;

    return (
        <div className="mt-3 space-y-2">
            {probabilities && (
                <ul className="text-xs text-gray-600 flex flex-wrap gap-x-4 gap-y-1">
                    {Object.entries(probabilities).sort(([, a], [, b]) => b - a).map(([label, probability]) => (
                        <li key={label}>{labelOf(label).text}: <strong>{formatProbability(probability)}</strong></li>
                    ))}
                </ul>
            )}
            <ul className="text-xs text-gray-500 flex flex-wrap gap-x-4 gap-y-1">
                {Object.entries(others).map(([key, value]) => (
                    <li key={key}>{key}: {String(value)}</li>
                ))}
            </ul>
        </div>
    );
};

const Chunk = ({ chunk }) => {
    const label = labelOf(chunk.label);

    return (
        <li className={`border rounded-lg p-4 ${chunk.used ? 'border-green-300 bg-white' : 'border-gray-200 bg-gray-50'}`}>
            <div className="flex flex-wrap items-center gap-2">
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${label.color}`}>{label.text}</span>
                <span className="text-xs font-medium text-gray-700">
                    {chunk.probability === null ? 'Sem probabilidade' : `Probabilidade: ${formatProbability(chunk.probability)}`}
                </span>
                <span className={`text-xs font-medium ${chunk.used ? 'text-green-700' : 'text-gray-500'}`}>
                    {chunk.used ? 'Usado na resposta' : 'Não usado'}
                </span>
            </div>
            <p className="mt-2 text-xs text-gray-500 break-words">{chunk.document_id}</p>
            <p className="mt-2 text-sm text-gray-800 whitespace-pre-wrap break-words">{chunk.content}</p>
            <ChunkDetails details={chunk.details} />
        </li>
    );
};

const ContextEvaluationDetail = ({ evaluation }) => (
    <div className="px-6 pb-6 pt-2 space-y-4">
        {evaluation.fallback_error && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-yellow-800">
                    <p className="font-medium">O avaliador configurado falhou e este resultado veio do avaliador de reserva.</p>
                    <p className="mt-1 break-words">{evaluation.fallback_error}</p>
                </div>
            </div>
        )}

        <div>
            <h3 className="text-sm font-semibold text-gray-900">Resposta</h3>
            <p className="mt-1 text-sm text-gray-800 whitespace-pre-wrap break-words">{evaluation.answer}</p>
        </div>

        <div>
            <h3 className="text-sm font-semibold text-gray-900">Contexto recuperado e avaliação</h3>
            <ol className="mt-2 space-y-3">
                {evaluation.chunks.map((chunk) => <Chunk key={chunk.position} chunk={chunk} />)}
            </ol>
        </div>

        <details>
            <summary className="text-sm font-semibold text-gray-900 cursor-pointer">Configuração do avaliador</summary>
            <dl className="mt-2 space-y-2">
                {Object.entries(evaluation.config).map(([key, value]) => (
                    <div key={key}>
                        <dt className="text-xs font-medium text-gray-500">{key}</dt>
                        <ConfigValue value={value} />
                    </div>
                ))}
            </dl>
        </details>
    </div>
);

export default ContextEvaluationDetail;
