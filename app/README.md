# TutorIA - Frontend React

## 🚀 Pré-requisitos

Antes de executar o projeto, certifique-se de ter instalado:

- **Node.js** (versão 16 ou superior) - [Download aqui](https://nodejs.org/)
- **npm** (vem com o Node.js) ou **yarn**

Para verificar se estão instalados:
```bash
node --version
npm --version
```

## 📦 Instalação e Configuração

### 1. Instale as dependências
```bash
npm install
```

Ou se preferir usar yarn:
```bash
yarn install
```

## ▶️ Executando o Projeto

### Modo Desenvolvimento
Para iniciar o servidor de desenvolvimento:
```bash
npm start
```

Ou com yarn:
```bash
yarn start
```

O projeto será executado em: `http://localhost:3000`

A página será recarregada automaticamente quando você fizer alterações no código.

### Build para Produção
Para criar uma build otimizada para produção:
```bash
npm run build
```

## 🔧 Configuração da API

⚠️ **IMPORTANTE**: O projeto está configurado para fazer requisições para o endpoint `/login`. 

### Opções de Configuração:

#### 1. Servidor Backend Local
Se você tem um servidor backend rodando localmente:
- Configure o proxy no `package.json` (já está incluído para `http://localhost:5000`)
- Ou altere a URL da requisição em `src/components/LoginPage.js`

#### 2. Servidor Backend Remoto
Edite o arquivo `src/components/LoginPage.js` e altere a linha:
```javascript
const response = await fetch('/login', {
```

Para:
```javascript
const response = await fetch('https://sua-api.com/login', {
```

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique se todas as dependências foram instaladas corretamente
2. Certifique-se de que a versão do Node.js é compatível
3. Verifique o console do navegador para erros JavaScript

## 📄 Licença

Este projeto é parte do sistema TutorIA para fins educacionais.

---

**Desenvolvido com ❤️ para o projeto TutorIA**
