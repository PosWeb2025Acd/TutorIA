const EVALUATOR_COLORS = {
    jev: 'bg-purple-100 text-purple-800',
    llm: 'bg-blue-100 text-blue-800',
};
const DEFAULT_COLOR = 'bg-gray-100 text-gray-800';

const EvaluatorBadge = ({ evaluator }) => (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${EVALUATOR_COLORS[evaluator] || DEFAULT_COLOR}`}>
        {evaluator.toUpperCase()}
    </span>
);

export default EvaluatorBadge;
