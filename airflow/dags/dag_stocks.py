from airflow.decorators import dag, task
from airflow.macros import ds_add
from airflow.utils.dates import days_ago

import yfinance as yf
from  pathlib import Path
import logging
import os

# Lista de tickers para baixar os dados 
TICKERS = [
            "AAPL",
            "MSFT",
            "GOOG",
            "TSLA"

            ]
@task()
def get_history(ticker, ds=None, ds_nodash=None): 
    """
    Baixa o histórico de preços de uma ação específica usando yfinance e salva em CSV.
    obs: atençao ao caminho do arquivo, deve existir a pasta 'data/stock/{ticker}/' no diretório airflow
    1. Cria o diretório se não existir. 

    """
    try:
        file_path = f'/opt/airflow/data/web/stock/{ticker}/{ticker}_{ds_nodash}.csv'
        Path(file_path).parent.mkdir(parents=True, exist_ok=True) 
        yf.Ticker(ticker).history(
            period ="1d",
            interval = "1h",
            start = ds_add(ds, -1) ,
            end = ds ,
            prepost = True
        ).to_csv(file_path)
        logging.info(f"Dados para {ticker} em {ds} baixados com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao baixar dados para {ticker} em {ds}: {e}") 
        raise

@dag(
    dag_id = "dag_stocks",
    schedule_interval = "0 0 * * 2-6", # de terça a sábado
    start_date = days_ago(1),
    catchup = False
)
def dag_stocks():
    for ticker in TICKERS:
        get_history.override(task_id=f"get_history_{ticker}")(ticker)

dag = dag_stocks()