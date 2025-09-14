#!/bin/sh

# SHOULD BE EXECUTED ONLY AT THE FIRST TIME RUNNING THE PROJECT

docker compose up -d

OLLAMA_SERVICE="ollama"
RAG_SERVICE="api"
LLM_LLAMA_MODEL="llama3.1:8b"

OLLAMA_CONTAINER_ID=$(docker compose ps -q "$OLLAMA_SERVICE")
RAG_CONTAINER_ID=$(docker compose ps -q "$RAG_SERVICE")

if docker ps -q --no-trunc | grep -q "$OLLAMA_CONTAINER_ID"; then
    printf "Ollama is running. Pulling LLMs: $LLM_LLAMA_MODEL"
    docker compose exec -it $OLLAMA_SERVICE ollama pull $LLM_LLAMA_MODEL
else
    printf "Ollama container is not running. Check if is a service running at the port 11434."
fi

if docker ps -q --no-trunc | grep -q "$RAG_CONTAINER_ID"; then
    printf "\nRAG app is running"
    docker compose exec -it $RAG_SERVICE ./app/scripts/init_checkpointer.sh
else
    printf "\nRAG app is not running"
fi
