# Configuração do Ambiente

Este documento detalha os passos necessários para configurar e executar o ambiente de desenvolvimento do projeto `maestro-airflow`.

## Pré-requisitos

Antes de iniciar, certifique-se de ter os seguintes softwares instalados em sua máquina:

*   **Docker Desktop:** Essencial para construir e executar os serviços do Airflow e PostgreSQL.
    *   [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
*   **Docker Compose:** Geralmente vem incluído com o Docker Desktop.
*   **Git:** Para clonar o repositório.

## Passos de Configuração

1.  **Clonar o Repositório:**

    ```bash
    git clone https://github.com/seu-usuario/maestro-airflow.git
    cd maestro-airflow
    ```

2.  **Configurar Variáveis de Ambiente:**

    Crie um arquivo `.env` na raiz do projeto, copiando o `.env-example`. Preencha as variáveis com seus valores desejados.

    ```bash
    cp .env-example .env
    # Edite o arquivo .env com suas credenciais e configurações
    ```

    Exemplo de `.env`:

    ```
    AIRFLOW_IMAGE_NAME=maestro-airflow:latest
    AIRFLOW_USER=admin
    AIRFLOW_PASSWORD=admin
    AIRFLOW_FIRST_NAME=Admin
    AIRFLOW_EMAIL=admin@example.com

    POSTGRES_USER=airflow
    POSTGRES_PASSWORD=airflow
    POSTGRES_DB=airflow
    ```

3.  **Construir as Imagens Docker:**

    Este comando irá construir as imagens Docker para o Airflow, utilizando as configurações do `Dockerfile` e `docker-compose.yml`.

    ```bash
    docker-compose build
    ```

4.  **Iniciar os Serviços:**

    Após a construção das imagens, inicie os serviços do Airflow e PostgreSQL.

    ```bash
    docker-compose up -d
    ```

    Este comando irá:
    *   Iniciar o contêiner do PostgreSQL.
    *   Aguardar o PostgreSQL estar saudável.
    *   Executar as migrações do banco de dados do Airflow.
    *   Criar o usuário administrador do Airflow (se não existir).
    *   Iniciar o servidor web do Airflow.
    *   Iniciar o scheduler do Airflow.

5.  **Acessar a UI do Airflow:**

    Após os serviços estarem em execução, você pode acessar a interface do usuário do Airflow em:

    [http://localhost:8080](http://localhost:8080)

    Use as credenciais definidas no seu arquivo `.env` para fazer login.

## Próximos Passos

*   Explore os DAGs na pasta `airflow/dags`.
*   Comece a desenvolver seus próprios pipelines de dados.
