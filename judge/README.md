# Judge for answers

### Dados para avaliação

Combinação do contexto recuperado com a resposta obtida para a avaliação da resposta

### Formato de avaliação

- Geração de Pontuação
- Sim/Não resposta
- Comparação em pares (Avalia qual a melhor opção entre um PAR)
- RAG TRIAD (Estudar)

### LLM

- [JudgeLM](https://huggingface.co/BAAI/JudgeLM-7B-v1.0)


### LLM as a judge for agents (A Survey on LLM-as-a-Judge)

2.4.3 LLM-as-a-Judge for Agents. There are two ways to apply LLM-as-a-Judge for an agent.
One is to evaluate the entire process of the intelligent agent [225], and the other is to evaluate it at
a specific stage in the agent framework process [47, 131]. Both approaches are briefly illustrated in
Figure 10. Using LLM as the brain of agent, an agentic system [225] could evaluate like a human, it
would reduce the need for human involvement and eliminate the trade-off between thoroughness
and effort. In addition, the agent [131] can interact with the environment through language and
receive feedback on actions through LLM to make decisions for the next action