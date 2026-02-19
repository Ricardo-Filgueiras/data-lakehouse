from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook # Ou MySqlHook, dependendo do seu banco
from airflow.operators.empty import EmptyOperator
from datetime import datetime
from pathlib import Path
import pandas as pd

def extrair_vendas_para_csv(ds, conn_id):
    # 1. Definir estrutura de pastas dinâmica
    ano = ds.split('-')[0]
    file_path = Path(f'/opt/airflow/data/vendas/{ano}/{ds}.csv')
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # 2. Conectar ao banco usando o Hook do Airflow
    hook = PostgresHook(postgres_conn_id=conn_id)
    
    # 3. Query SQL para obter os dados (sem criar tabela no banco, apenas lendo)
    sql = """
        SELECT
            nome_atendente,
            SUM(valor_un * quantidade) AS total_vendas
        FROM vendas
        WHERE CAST(data_venda AS DATE) = '{}' -- Exemplo de filtro por data
        GROUP BY nome_atendente;
    """.format(ds)

    # 4. Carregar os dados para um DataFrame e salvar em CSV
    df = hook.get_pandas_df(sql)
    
    if not df.empty:
        df.to_csv(file_path, index=False)
        print(f"Arquivo salvo com sucesso em: {file_path}")
    else:
        print(f"Nenhum dado de venda encontrado para a data {ds}")

with DAG(
    dag_id="dag_vendas_para_csv",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
) as dag:

    inicio = EmptyOperator(task_id='inicio')
    
    extrair_vendas = PythonOperator(
        task_id='extrair_vendas_sql',
        python_callable=extrair_vendas_para_csv,
        op_kwargs={
            'ds': '{{ ds }}',
            'conn_id': 'insight_places'
        }
    )
    fim = EmptyOperator(task_id='fim')

    inicio >> extrair_vendas >> fim