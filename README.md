# ACD V3

V3 uses langgraph

### Chat History

To achieve that we will use short term memory. Short-term memory lets your application
remember previous interactions within a single thread or conversation. , 

- Semantic memory, both in humans and AI agents, involves the retention of specific facts and concepts. For AI agents, semantic memory is often used to personalize applications by remembering facts or concepts from past interactions.

- Episodic memory, in both humans and AI agents, involves recalling past events or actions. In practice, episodic memories are often implemented through few-shot example prompting, where agents learn from past sequences to perform tasks correctly

- Procedural memory, in both humans and AI agents, involves remembering the rules used to perform tasks
procedural memory is a combination of model weights, agent code, and agent's prompt that collectively
determine the agent's functionality.

### Corrective Retrieve Augmented Generation

The correct retrieve augmented generation evalutes the relevance of the documents retrieved based on the user question, and than if necessary, provides
a fallback mechanism to search for relevant documents from another source.

### ChromaDB

Conexão do chromadb com mysql: Aparentemente, não há suporte para comunicação com mysql. Talvez, teriamos que fazer algo como criar uma adaptação do chroma db que extenda a classe do chromadb para estabelecer uma comunicação direta com o mysql (https://github.com/chroma-core/chroma/issues/1055)

### RAG Architecture

![RAG Architecture](images/Tutor%20IA%20-%20ACD%20Rag.png)

