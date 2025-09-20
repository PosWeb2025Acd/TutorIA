#!/bin/sh

printf "Stopping and removing containers and db volumes...\n"
docker compose down

printf "Removing volumes...\n"
docker volume rm tutoria_db
