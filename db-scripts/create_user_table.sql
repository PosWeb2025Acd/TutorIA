CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario VARCHAR(255) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP NULL
);

-- Índice para otimizar consultas por usuário
CREATE INDEX idx_usuarios_usuario ON usuarios(usuario);
