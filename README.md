# Data Lakehouse Project

Este projeto implementa uma arquitetura de **Data Lakehouse** moderna e modular, utilizando ferramentas de código aberto para orquestração, armazenamento e processamento de dados. A estrutura foi desenhada para ser executada em containers Docker de forma independente, mas interconectada.

##  Arquitetura

O projeto é dividido em três camadas principais:

1.  **Orquestração (Airflow):** Responsável pelo agendamento e execução de pipelines de dados (ELT/ETL).
2.  **Motor de Consulta (Trino):** Camada de computação distribuída que permite consultar dados em diferentes fontes e formatos (S3/MinIO, Postgres, SQL Server) usando SQL padrão.
3.  **Armazenamento e Metadados (MinIO & Hive Metastore):** 
    *   **MinIO:** Armazenamento de objetos compatível com S3 (Camadas Landing, Bronze, Silver, Gold).
    *   **Hive Metastore:** Gerenciamento de metadados para tabelas Delta, Iceberg e Hive.
4.  **Visualização (Power BI):** Inclui um conector customizado para integração entre o Power BI e o motor Trino.

##  Estrutura do Repositório

```text
data-lakehouse/
├── airflow/            # Orquestração com Apache Airflow
│   ├── dags/           # Pipelines de dados (Python)
│   └── docker-compose/ # Infraestrutura do Airflow
├── trino/              # Motor de consulta e infra do Lakehouse
│   ├── conf/           # Configurações de catálogos (Delta, Iceberg, etc)
│   ├── metastore/      # Configurações do Hive Metastore
│   └── query/          # Scripts SQL de exemplo e criação de tabelas
└── powerbi-trino-connector/ # Conector customizado para Power BI
```

##  Tecnologias Utilizadas

*   **Apache Airflow 3.x**
*   **Trino (antigo PrestoSQL)**
*   **MinIO** (S3 Storage)
*   **Hive Metastore**
*   **MariaDB** (para metastore)
*   **Power BI** (via conector customizado)

##  Como Executar

### Pré-requisitos
*   Docker e Docker Compose instalados.
*   Criação manual da rede Docker para comunicação entre os módulos:

```bash
docker network create src_lakehouse
```

### 1. Subindo o Data Lake (Trino + MinIO)
Navegue até a pasta do Trino e inicie os serviços:
```bash
cd trino
docker-compose up -d
```
Isso criará automaticamente os buckets necessários no MinIO (`landing`, `bronze`, `silver`, `gold`).

### 2. Subindo o Orquestrador (Airflow)
Navegue até a pasta do Airflow e inicie os serviços:
```bash
cd ../airflow
docker-compose up -d
```

##  Portas de Acesso

| Serviço | Porta | Descrição |
| :--- | :--- | :--- |
| **Airflow** | `8083` | Interface Web do Orquestrador |
| **Trino** | `8080` | Console do Motor de Consulta |
| **MinIO Console**| `9001` | Interface Web do Storage |
| **Flower** | `5555` | Monitoramento de Workers Airflow |

##  Automação (Provisionamento Reprodutível)

1. Crie o arquivo de variáveis de ambiente:
   - `cp .env.example .env`
   - `cp trino/.env.example trino/.env`
   - `cp airflow/.env.example airflow/.env`
2. Ajuste os valores sensíveis no `.env`.
3. Execute o script de inicialização:
   - Linux/macOS: `bash scripts/start.sh`
   - Windows: `powershell -File scripts/start.ps1`

##  Notas de Manutenção
Os serviços foram separados em pastas diferentes para permitir manutenções isoladas. Você pode derrubar o Airflow para atualizar uma biblioteca sem afetar a disponibilidade do Trino ou do Storage.
