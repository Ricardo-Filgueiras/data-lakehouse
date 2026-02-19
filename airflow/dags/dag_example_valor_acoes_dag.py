from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.macros import ds_add
from datetime import datetime, timedelta
from pathlib import Path
import yfinance as yf
import pandas as pd

# Funções de extração adaptadas
def get_history_stock(ticker, ds, ds_nodash):
    # Definindo o caminho dentro do container
    ano = ds.split('-')[0] 
    
    file_path = Path(f'/opt/airflow/data/stock/{ano}/{ticker}/{ticker}_{ds_nodash}.csv')
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Fazendo a chamada ao yfinance
    # start = dia anterior, end = dia da execução (ds)
    df = yf.Ticker(ticker).history(
        period="1d",
        interval="1h",
        start=ds_add(ds, -1),
        end=ds,
        prepost=True
    )
    
    if not df.empty:
        df.to_csv(str(file_path))
    else:
        print(f"Nenhum dado encontrado para {ticker} em {ds}")

# Configuração da DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'dag_extracao_acoes',
    default_args=default_args,
    schedule_interval='@daily',  # Executa uma vez por dia
    catchup=False
) as dag:

    inicio = EmptyOperator(task_id='inicio')

    # Lista de ativos que você quer monitorar
    tickers = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA']

    # Criando a lista de tarefas via loop
    tasks = []
    for ticker in tickers:
        task_id = f'get_history_{ticker.replace(".", "_")}'
        
        t = PythonOperator(
            task_id=task_id,
            python_callable=get_history_stock,
            op_kwargs={
                'ticker': ticker,
                'ds': '{{ ds }}',
                'ds_nodash': '{{ ds_nodash }}'
            }
        )
        tasks.append(t)

    fim = EmptyOperator(task_id='fim')

    inicio >> tasks >> fim

