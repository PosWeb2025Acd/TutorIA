# TutorIA

### Primeira vez no projeto

Execute o arquivo .init.sh
```bash
./init.sh
```
Esse arquivo irar subir os container e executar algumas migrações necessárias pela primeira vez

### Ollama

O Ollama do projeto roda em container e fica publicado na porta **11435** da máquina, para não conflitar com um Ollama instalado localmente, que usa a 11434. No `.env`, mantenha `OLLAMA_URL=http://ollama-tutoria:11434`: essa é a porta interna, usada pelos serviços dentro do Docker.

Se o `docker compose ps` mostrar o `ollama` como `unhealthy`, libere a porta 11435 e recrie o container:
```bash
docker compose up -d --force-recreate ollama
```

### Links Importantes

[Nvidia Docker Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) - Habilita uso da GPU por parte de containers docker
