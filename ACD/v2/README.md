# ACD V2

### Chat History

To achieve that we will use short term memory. Short-term memory lets your application
remember previous interactions within a single thread or conversation. , 

- Semantic memory, both in humans and AI agents, involves the retention of specific facts and concepts. For AI agents, semantic memory is often used to personalize applications by remembering facts or concepts from past interactions.

- Episodic memory, in both humans and AI agents, involves recalling past events or actions.
In practice, episodic memories are often implemented through few-shot example prompting, where
agents learn from past sequences to perform tasks correctly

- Procedural memory, in both humans and AI agents, involves remembering the rules used to perform tasks
procedural memory is a combination of model weights, agent code, and agent's prompt that collectively
determine the agent's functionality.

### ChromaDB

Conexão do chromadb com mysql: Aparentemente, não há suporte para comunicação com mysql. Talvez, teriamos que fazer algo como criar uma adaptação do chroma db que extenda a classe do chromadb para estabelecer uma comunicação direta com o mysql (https://github.com/chroma-core/chroma/issues/1055)



