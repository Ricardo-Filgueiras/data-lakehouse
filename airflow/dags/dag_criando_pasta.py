from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from os.path import join
from utils import extracao 

import pendulum
import os


with DAG(
            'criando_pasta_bash',
            start_date=pendulum.today('UTC').add(days=-1),
            schedule='@daily'
) as dag:

        inicio = EmptyOperator(task_id='inicio')

        tarefa01 = BashOperator(
            task_id='criar_pasta',
            bash_command='mkdir -p /data/dollar',
        )

        fim = EmptyOperator(task_id='fim')

        inicio >> tarefa01 >> fim