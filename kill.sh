#!/bin/sh

docker compose down
docker volume rm tutoria_db
docker volume rm tutoria_ollama_data
