import datetime
import os

from airflow.decorators import dag, task
from airflow.exceptions import AirflowSkipException
from airflow.providers.postgres.hooks.postgres import PostgresHook

import duckdb
import pandas as pd

# DAG para ler dados do MinIO usando DuckDB e inserir no banco analítico PostgreSQL

# Configura variáveis de ambiente; em produção use Airflow Connections / Secret Backends.
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://localhost:9000")
POSTGRES_CONN_ID = os.getenv("POSTGRES_CONN_ID", "postgres_default")

@dag(
    dag_id="minio_to_analytics",
    start_date=datetime.datetime(2021, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args={
        "owner": "airflow",
        "retries": 1,
        "retry_delay": datetime.timedelta(minutes=10),
        # "email_on_failure": False,
    },
    tags=["minio", "duckdb", "postgres"],
)
def minio_to_analytics_dag():

    @task(retries=2, retry_delay=datetime.timedelta(minutes=5))
    def extract_from_minio():
        con = duckdb.connect(":memory:")

        con.execute("INSTALL httpfs;")
        con.execute("LOAD httpfs;")

        con.execute(f"""
            SET s3_endpoint='{AWS_ENDPOINT_URL}';
            SET s3_region='{AWS_REGION}';
            SET s3_access_key_id='{AWS_ACCESS_KEY_ID}';
            SET s3_secret_access_key='{AWS_SECRET_ACCESS_KEY}';
            SET s3_use_ssl=false;
            SET s3_url_style='path';
        """)

        partition_path = 's3://landing/codemp=*/codvend=*/dtneg=*/numnota=*/arquivo.csv'

        try:
            df = con.execute(
                f"SELECT * FROM read_csv_auto('{partition_path}', HEADER=True, SAMPLE_SIZE=100000, IGNORE_ERRORS=True)"
            ).df()
        except Exception as err:
            raise RuntimeError("Falha ao ler arquivos do MinIO via DuckDB") from err

        if df is None or df.empty:
            raise AirflowSkipException("Não há dados a processar no caminho informado")

        return df

    @task(retries=1)
    def load_to_postgres(df):
        if df is None or (hasattr(df, 'empty') and df.empty):
            raise AirflowSkipException("DataFrame vazio, não há dados para carregar")

        hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        engine = hook.get_sqlalchemy_engine()

        df.to_sql(
            "fvendas",
            engine,
            schema="analytics",
            if_exists="replace",
            index=False,
            method="multi",
        )

        return len(df)

    df = extract_from_minio()
    records = load_to_postgres(df)

    return records

minio_to_analytics = minio_to_analytics_dag()
