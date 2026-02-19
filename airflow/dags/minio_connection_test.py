from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator

def test_minio_connection():
    """
    Tenta se conectar ao MinIO usando a conexão definida no Airflow
    e lista os buckets existentes.
    """
    try:
        # O 's3_conn_id' deve corresponder ao ID da conexão criada no Airflow.
        # No seu docker-compose, a variável de ambiente é AIRFLOW_CONN_MINI,
        # então o Airflow cria uma conexão com o ID 'mini'.
        hook = S3Hook(aws_conn_id='mini_defalt')
        s3_client = hook.get_conn()
        print("Conexão com o MinIO obtida com sucesso.")

        response = s3_client.list_buckets()
        bucket_names = [bucket["Name"] for bucket in response.get("Buckets", [])]

        if bucket_names:
            print("Buckets existentes:")
            for name in bucket_names:
                print(f"- {name}")
        else:
            print("Nenhum bucket encontrado.")

        print("Teste de conexão com o MinIO bem-sucedido!")

    except Exception as e:
        print(f"Falha ao conectar ou listar buckets no MinIO: {e}")
        raise

with DAG(
    dag_id="minio_connection_test",
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"),
    catchup=False,
    schedule=None,
    tags=["minio", "test"],
) as dag:
    PythonOperator(
        task_id="test_s3_connection",
        python_callable=test_minio_connection,
    )
