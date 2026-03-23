-- Script de inicialização do banco analítico
-- Este banco recebe dados tratados pelo Trino e armazena dados modelados em star schema

-- Criar schema para dados analíticos
CREATE SCHEMA IF NOT EXISTS analytics;

-- Tabela de dimensão: Tempo
CREATE TABLE IF NOT EXISTS analytics.dim_tempo (
    id_tempo SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    ano INTEGER NOT NULL,
    mes_abre VARCHAR(20) NOT NULL CHECK (mes_abre IN ('Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez')),
    nome_mes VARCHAR(20) NOT NULL,
    mes_num INTEGER NOT NULL CHECK (mes_num BETWEEN 1 AND 12),
    ano_mes INT NOT NULL,
    trimestre INT NOT NULL,
    trimestre_abreviado VARCHAR(10) NOT NULL,
    bimestre INT NOT NULL,
    semestre INT NOT NULL,
    semana INT NOT NULL,
    dia_semana INTEGER NOT NULL,
    nome_dia_sem VARCHAR(20) NOT NULL
);

-- Adiciono um índice para melhorar o desempenho das consultas
CREATE INDEX idx_data ON analytics.dim_tempo (data);

-- Tabela de fato: Vendas
CREATE TABLE IF NOT EXISTS analytics.fato_vendas (
    id_venda SERIAL PRIMARY KEY,
    id_tempo INTEGER NOT NULL REFERENCES analytics.dim_tempo(id_tempo),
    id_produto INTEGER NOT NULL REFERENCES analytics.dim_produto(id_produto),
    id_cliente INTEGER NOT NULL REFERENCES analytics.dim_cliente(id_cliente),
    quantidade INTEGER NOT NULL,
    valor_total DECIMAL(15,2) NOT NULL,
    desconto DECIMAL(10,2) DEFAULT 0,
    data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


