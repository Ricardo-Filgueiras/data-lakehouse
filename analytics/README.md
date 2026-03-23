# Banco de Dados Analítico

Este diretório contém a configuração e estrutura do banco de dados analítico baseado em PostgreSQL, projetado para receber dados tratados pelo Trino e armazenar dados modelados em star schema para servir dashboards e análises.

## Papel do Banco Analítico

### O que NÃO deve ser:
- Repositório bruto de dados
- Receber arquivos CSV diretamente
- Ser usado como staging de dados sujos

### O que DEVE ser:
- Receber dados já tratados e limpos pelo Trino
- Armazenar dados modelados (tabelas fato + dimensões)
- Servir dashboards e consultas analíticas

## Estrutura

### Docker Compose
- `docker-compose.yml`: Configuração do serviço PostgreSQL
  - Porta: 5433 (para evitar conflito com outros PostgreSQL)
  - Banco: analytics_db
  - Rede: src_lakehouse (compartilhada com outros serviços)

### Scripts de Inicialização
- `init-scripts/01_create_analytics_schema.sql`: Criação das tabelas em star schema
  - **Dimensões**:
    - `dim_tempo`: Dados temporais
    - `dim_produto`: Informações de produtos
    - `dim_cliente`: Dados de clientes
  - **Fato**:
    - `fato_vendas`: Vendas realizadas

## Como Usar

1. Certifique-se de que a rede `src_lakehouse` existe (criada pelos outros serviços)
2. Configure as variáveis de ambiente no arquivo `.env`:
   ```
   POSTGRES_ANALYTICS_USER=seu_usuario
   POSTGRES_ANALYTICS_PASSWORD=sua_senha
   ```
3. Execute: `docker-compose up -d`
4. O banco estará disponível na porta 5433

## Integração com Trino

O Trino já está configurado para conectar a este banco através do catálogo `postgres` (ver `trino/conf/postgres.properties`). Os dados tratados no Trino podem ser inseridos neste banco analítico via queries SQL.

## Próximos Passos

- Configurar conexões no Airflow para inserir dados tratados
- Criar DAGs para ETL do Trino para PostgreSQL Analytics
- Desenvolver dashboards conectados a este banco