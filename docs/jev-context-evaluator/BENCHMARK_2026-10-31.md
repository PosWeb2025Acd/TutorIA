# Benchmark de avaliação de contexto: JEV x LLM (31/10/2026)

Resultados e conclusões da rodada de 31/10/2026 do comparativo entre os avaliadores de contexto do TutorIA. A arquitetura, a análise de viabilidade do JEV e a metodologia estão em [JEV_CONTEXT_EVALUATOR.md](JEV_CONTEXT_EVALUATOR.md).

- **Arquivos da rodada:** `rag/benchmark/results/benchmark_20261031_185718.json`, `.md` e `_predictions.csv`
- **Dataset:** `rag/benchmark/data/dataset.csv`, com 168 pares pergunta–chunk (42 perguntas × top-4)
- **Gabarito:** 38 `relevant`, 58 `partially_relevant`, 72 `not_relevant`

## Resumo

- **Tempo:** o JEV avaliou o contexto de uma pergunta em **0,24 s**, contra **9,62 s** do LLM. É cerca de **40× mais rápido** em paralelo (como roda em produção) e cerca de 11× mais rápido um chunk por vez.
- **Assertividade por chunk:**
  - **Acurácia:** 0,815 no JEV contra 0,613 no LLM.
  - **Macro-F1:** 0,814 contra 0,538.
  - **Kappa contra o gabarito:** 0,71 contra 0,41.

  A diferença é **estatisticamente significativa** (McNemar, p < 0,001).
- **Decisão de responder ou recusar:** acurácia de 0,929 no JEV contra 0,857 no LLM. O JEV **nunca respondeu sem contexto relevante**, e o LLM fez isso 3 vezes. A diferença **não é significativa** com 42 perguntas (McNemar exato, p ≈ 0,45).
- **Perfis de erro opostos:** o LLM deixa passar contexto parcial (precisão de `relevant` de 0,47). O JEV é conservador (precisão de 1,00), mas às vezes barra contexto bom (recall de 0,71).
- **Custo do JEV:** US$ 0,0135 pelas 504 avaliações, cerca de US$ 0,0001 por pergunta.
- **Principal ressalva:** 160 dos 168 rótulos do gabarito foram atribuídos por um modelo (Claude), não por uma pessoa (ver [Ameaças à validade](#ameaças-à-validade)).

## Ambiente

| Item | Valor |
|---|---|
| Data | 31/10/2026 |
| LLM | `llama3.1:8b` via Ollama 0.11.10, temperatura 0 |
| GPU do Ollama | NVIDIA GeForce RTX 2050, 3,7 GB de VRAM. O Ollama entrou em *low vram mode*, e o modelo (4,9 GB) não cabe inteiro na GPU |
| JEV | `jev-1.13.0` (API TypeSafe), Score com 3 níveis, argmax das probabilidades |
| Modos | `llm` (sequencial), `jev_sequential` (1 requisição por vez), `jev_parallel` (4 requisições simultâneas) |
| Repetições | 3, depois de um warm-up que fica fora da medição |
| Erros | 0 nos três modos |

A rodada de 20/10/2026 (`benchmark_20261020_020451`) foi **descartada**. Naquela execução, todas as 504 chamadas do modo `llm` falharam porque o container do Ollama estava sem rede. As falhas foram contadas como `not_relevant`, e as métricas do LLM ficaram sem sentido.

## Tempo

| | LLM | JEV sequencial | JEV paralelo |
|---|---|---|---|
| Por chunk, média | 2,41 s | 0,21 s | 0,06 s |
| Por chunk, p95 | 4,51 s | 0,25 s | 0,07 s |
| Por chunk, mín–máx | 1,58–8,67 s | — até 0,60 s | 0,05–0,19 s |
| Por pergunta (4 chunks), média | 9,62 s | 0,85 s | 0,24 s |
| Por pergunta, p95 | 14,48 s | — | 0,29 s |
| Retrieval + avaliação, média | 9,67 s | 0,90 s | 0,29 s |
| Tempo total das 3 repetições | 1.212 s | — | 30 s |

- O retrieval é igual para todos os modos (cerca de 0,05 s) e é desprezível perto da avaliação.
- O JEV é rápido e também **previsível**: a latência dele quase não varia. A do LLM varia mais de 5× entre o chunk mais rápido e o mais lento.
- O paralelismo multiplica a vantagem, porque cada chunk é uma requisição independente. No Ollama local, com uma GPU, as chamadas acabam serializadas.
- A latência do LLM está **inflada pelo hardware**, porque o modelo não cabe na VRAM. Numa GPU maior a diferença diminuiria, mas não foi medida. A latência do JEV inclui a ida e volta pela internet.

## Assertividade por chunk

| | LLM | JEV |
|---|---|---|
| Acurácia (3 classes) | 0,613 | **0,815** |
| Macro-F1 | 0,538 | **0,814** |
| Kappa contra o gabarito | 0,411 | **0,710** |
| Acurácia binária (`relevant` contra o resto) | 0,750 | **0,935** |

Por classe:

| Classe | LLM, P / R / F1 | JEV, P / R / F1 | Suporte |
|---|---|---|---|
| `relevant` | 0,47 / 0,82 / 0,60 | **1,00** / 0,71 / **0,83** | 38 |
| `partially_relevant` | 0,67 / 0,14 / 0,23 | 0,71 / **0,78** / **0,74** | 58 |
| `not_relevant` | 0,71 / 0,89 / 0,79 | **0,83** / **0,90** / **0,87** | 72 |

Matrizes de confusão (linha = gabarito; colunas = `relevant`, `partially_relevant`, `not_relevant`):

| Gabarito | LLM | JEV |
|---|---|---|
| `relevant` | 31 · 1 · 6 | 27 · 11 · 0 |
| `partially_relevant` | **30** · 8 · 20 | 0 · 45 · 13 |
| `not_relevant` | 5 · 3 · 64 | 0 · 7 · 65 |

- **LLM:** marcou 30 dos 58 chunks parciais como `relevant` e quase nunca usa a classe intermediária (recall de 0,14). Esse comportamento é coerente com o prompt atual, que pede um teste não rigoroso, por palavras-chave (*"It does not need to be a stringent test"*).
- **JEV:** nunca marcou como `relevant` um chunk que não era. O erro dominante é rebaixar 11 chunks relevantes para `partially_relevant`.
- **Significância:** na decisão binária por chunk, houve 38 chunks em que só o JEV acertou e 7 em que só o LLM acertou (McNemar χ² ≈ 20, p < 0,001).
- **Concordância entre os avaliadores:** kappa de 0,406. As discordâncias são sistemáticas, não ruído.

## Decisão de responder ou recusar

O grafo só gera resposta se houver pelo menos um chunk `relevant`.

| | LLM | JEV |
|---|---|---|
| Acurácia do gate | 0,857 (36/42) | **0,929** (39/42) |
| Respondeu corretamente | 22 | 22 |
| Recusou corretamente | 14 | **17** |
| Respondeu sem contexto relevante | 3 | **0** |
| Recusou tendo contexto relevante | 3 | 3 |

Perguntas em que algum avaliador errou o gate:

| Pergunta | Tipo | Gabarito | LLM | JEV | Observação |
|---|---|---|---|---|---|
| q02: diferença entre herança e composição | corpus | responde | responde | recusa | Os chunks explicam herança, mas não composição. P(relevant) do JEV ≤ 0,01 |
| q06: características da programação funcional | corpus | recusa | **responde** | recusa | O LLM aceitou chunks introdutórios como relevantes |
| q09: normalização em banco de dados | corpus | recusa | **responde** | recusa | O LLM aceitou a página de título de uma apostila |
| q13: vantagens de microsserviços | corpus | responde | responde | recusa | Rótulo de fronteira no gabarito. P(relevant) do JEV = 0,12 |
| q15: o que é SOA | corpus | recusa | **responde** | recusa | Os chunks são sobre um estudo de caso de SOA, sem definição |
| q23: diferença entre pilha e fila | corpus | responde | recusa | recusa | Os chunks falam só de pilha |
| q40: NoSQL "não suporta consultas" | premissa falsa | responde | recusa | responde | O chunk sobre chave-valor contradiz a premissa |
| q41: Scrum "sem Product Owner" | premissa falsa | responde | recusa | responde | Os chunks descrevem o papel do PO |

- **LLM:** os erros do tipo "respondeu sem contexto" (q06, q09, q15) são os mais graves para um RAG corretivo, porque abrem espaço para alucinação. O LLM também marcou todos os chunks das perguntas com premissa falsa como `not_relevant`, recusando justamente quando havia contexto para corrigir o aluno.
- **JEV:** os 3 erros (q02, q13, q23) vêm da leitura literal de perguntas comparativas ("diferença entre A e B"). Um chunk que explica só A foi classificado como parcial. A documentação do JEV avisa sobre essa literalidade. O gabarito foi mais leniente, e dá para defender os dois critérios.
- **Significância:** a vantagem do JEV no gate se resume a 5 perguntas contra 2 (McNemar exato, p ≈ 0,45). Não é estatisticamente significativa com esta amostra.

## Recortes

| Recorte | n chunks | LLM, acurácia / binária | JEV, acurácia / binária |
|---|---|---|---|
| Perguntas no corpus | 136 | 0,588 / 0,721 | 0,801 / 0,934 |
| Fora do corpus | 20 | 0,950 / 1,000 | 1,000 / 1,000 |
| Premissa falsa | 12 | 0,333 / 0,667 | 0,667 / 0,833 |
| Chunks em PT | 162 | 0,630 / 0,772 | 0,815 / 0,932 |
| Chunks em EN | 6 | 0,167 / 0,167 | 0,833 / 1,000 |

- **Fora do corpus:** nenhum dos dois respondeu indevidamente.
- **Idioma:** a documentação do JEV indica o inglês como língua principal, mas o desempenho em português foi alto (0,815). Só 6 chunks foram detectados como inglês, então **não dá para tirar conclusão sobre idioma** desta rodada.

## Limiar de P(relevant) do JEV

Rótulo `relevant` quando P(relevant) ≥ limiar:

| Limiar | Acurácia binária | Precisão | Recall | F1 |
|---|---|---|---|---|
| 0,7 | 0,905 | 1,00 | 0,58 | 0,73 |
| 0,6 | 0,911 | 1,00 | 0,61 | 0,75 |
| 0,5 (aproximadamente o argmax atual) | 0,935 | 1,00 | 0,71 | 0,83 |
| 0,4 | 0,952 | 1,00 | 0,79 | 0,88 |
| **0,3** | **0,964** | **1,00** | **0,84** | **0,91** |

- Baixar o limiar para 0,3 recupera recall **sem perder precisão**. O ganho está superestimado, porque o limiar foi escolhido olhando o próprio conjunto de teste; antes de adotar, é preciso validar em outro conjunto.
- O limiar **não resolve** os erros de gate (q02, q13, q23): nesses casos P(relevant) fica entre 0,01 e 0,12.
- Os chunks relevantes perdidos pelo JEV tiveram P(relevant) entre 0,01 e 0,49. A confiança média do JEV, considerando todas as respostas, foi de 0,85.

## Estabilidade e custo

| | LLM | JEV sequencial | JEV paralelo |
|---|---|---|---|
| Chunks com o mesmo rótulo nas 3 repetições | 100% | 99,4% (1 mudou) | 98,8% (2 mudaram) |
| Tokens de entrada (3 repetições) | — | — | 321.270 |
| Custo estimado | GPU local | — | US$ 0,0135 (cerca de US$ 0,0001 por pergunta) |

O LLM com temperatura 0 é determinístico. O JEV teve pequenas variações em chunks de fronteira.

## Ameaças à validade

1. **Gabarito produzido majoritariamente por modelo.** Dos 168 rótulos, 8 foram feitos pelo autor e 160 pelo Claude, seguindo o critério dessas 8 anotações. As descrições dos níveis do Score do JEV foram escritas pelo mesmo agente, com um critério parecido ("responde diretamente" contra "mesmo assunto, sem informação suficiente"). Isso pode favorecer o JEV. **Recomendação:** revisar o gabarito, ou ao menos uma amostra, e reportar a concordância entre a revisão humana e os rótulos atuais.
2. **A comparação é entre JEV e um prompt.** O prompt do LLM foi escrito para ser permissivo. Parte da diferença vem do critério do prompt, não só do modelo.
3. **Hardware e rede.** A GPU com pouca VRAM infla a latência do LLM, e a latência do JEV depende da rede. Os números de tempo valem para este ambiente.
4. **Amostra pequena.** São 42 perguntas, uma única fonte de retrieval (top-4 do Chroma) e só 6 chunks em inglês. As conclusões no nível do gate não têm significância estatística.
5. **Um único anotador** para as 8 anotações humanas, sem medida de concordância entre anotadores.

## Conclusões

1. **Tempo:** a vantagem do JEV é clara e robusta. Ele economiza cerca de 9,4 s por pergunta neste ambiente e tem latência estável. Mesmo numa GPU maior, o paralelismo por chunk continua sendo uma vantagem estrutural.
2. **Assertividade por chunk:** o JEV é significativamente melhor (macro-F1 de 0,81 contra 0,54) e, sobretudo, separa bem a classe intermediária, que o LLM praticamente ignora.
3. **Decisão final:** o JEV também foi melhor e eliminou as respostas sem contexto relevante. Mas a amostra não permite afirmar superioridade no gate com significância.
4. **Perfis complementares:** o LLM erra por permissividade (risco de alucinação). O JEV erra por literalidade (recusa perguntas comparativas). Para um tutor, o perfil conservador do JEV é preferível, desde que a recusa venha acompanhada de uma mensagem útil.
5. **Trade-offs operacionais:** o JEV depende de um serviço externo na nuvem e de uma chave de API, e os chunks saem da máquina. Hoje o grafo volta para o LLM em caso de falha da API.

## Próximos passos

- Revisar o gabarito (ameaça 1) e rodar o benchmark de novo.
- Acrescentar ao benchmark um modo `llm` com o mesmo critério dos níveis do JEV, para separar o efeito do modelo do efeito do prompt.
- Validar um limiar de P(relevant) em torno de 0,3 num conjunto separado de perguntas.
- Tratar perguntas comparativas: por exemplo, decompor "diferença entre A e B" em perguntas sobre A e sobre B, ou aceitar chunks parciais que cubram partes diferentes da pergunta.
- Medir a latência do LLM numa GPU que comporte o modelo inteiro.
