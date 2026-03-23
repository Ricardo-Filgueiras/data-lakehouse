"""
DAG para ler dados do MinIO usando DuckDB e inserir no banco analítico PostgreSQL
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.providers.amazon.aws.hooks.s3 import S3Hook  # Airflow 3.0.6 - providers.amazon.aws
import duckdb
import pandas as pd
from sqlalchemy import create_engine
import os

# Configurações
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'minio_to_analytics',
    default_args=default_args,
    description='Lê dados do MinIO com DuckDB e insere no PostgreSQL Analytics',
    schedule='@daily',  # Airflow 3.0.6 usa 'schedule' em vez de 'schedule_interval'
    start_date=datetime(2024, 1, 1),
    catchup=False,
)


def read_minio_with_duckdb(**context):
    """
    Lê arquivos CSV particionados do bucket 'teste01' do MinIO usando S3Hook e DuckDB
    """
    # Usar conector 'mini_defalt' do Airflow
    s3_hook = S3Hook(aws_conn_id='mini_defalt')
    
    bucket_name = 'teste01'
    prefix = ''  # Prefixo para filtrar arquivos (ex: 'vendas/')
    partition_columns = ['coluna01', 'coluna02', 'coluna03']
    
    try:
        # Listar arquivos no bucket
        files = s3_hook.list_keys(bucket_name=bucket_name, prefix=prefix)
        
        if not files:
            raise ValueError(f"Nenhum arquivo encontrado em s3://{bucket_name}/{prefix}")
        
        # Filtrar apenas arquivos CSV
        csv_files = [f for f in files if f.endswith('.csv')]
        
        print(f"✓ {len(csv_files)} arquivo(s) CSV encontrado(s)")
        
        # Ler todos os arquivos CSV e combinar
        dataframes = []
        
        for file_key in csv_files:
            # Baixar arquivo do MinIO
            file_content = s3_hook.read_key(
                bucket_name=bucket_name,
                key=file_key
            )
            
            # Ler CSV usando DuckDB
            conn = duckdb.connect(':memory:')
            
            # DuckDB pode ler CSV via pandas também
            import io
            df = pd.read_csv(io.StringIO(file_content))
            dataframes.append(df)
            
            print(f"  ✓ Lido: {file_key} ({len(df)} linhas)")
        
        # Combinar todos os dataframes
        df_combined = pd.concat(dataframes, ignore_index=True)
        
        print(f"✓ Dados lidos do MinIO via S3Hook")
        print(f"  Bucket: {bucket_name}")
        print(f"  Total de linhas: {len(df_combined)}")
        print(f"  Colunas: {list(df_combined.columns)}")
        print(f"  Partições esperadas: {partition_columns}")
        
        # Salvar dataframe no XCom para próxima task
        context['task_instance'].xcom_push(key='dataframe', value=df_combined)
        
        return {
            'status': 'success',
            'rows': len(df_combined),
            'columns': list(df_combined.columns),
            'files_read': len(csv_files)
        }
        
    except Exception as e:
        print(f"✗ Erro ao ler do MinIO: {str(e)}")
        raise


def transform_data(**context):
    """
    Transforma os dados CSV particionados usando DuckDB antes de inserir
    Trabalha com as colunas de partição: coluna01, coluna02, coluna03
    """
    # Recuperar dataframe da task anterior
    df = context['task_instance'].xcom_pull(
        task_ids='read_minio',
        key='dataframe'
    )
    
    partition_columns = ['coluna01', 'coluna02', 'coluna03']
    
    # Criar conexão DuckDB para transformação
    conn = duckdb.connect(':memory:')
    df_registered = conn.from_df(df)
    
    # Exemplo de transformação SQL com colunas de partição
    # Ajuste esta query conforme sua estrutura de dados real
    sql_query = f"""
        SELECT 
            *
        FROM df_registered
        WHERE 1=1
    """
    
    # Se as colunas de partição existem no dataframe, use-as no filtro
    existing_partition_cols = [col for col in partition_columns if col in df.columns]
    
    if existing_partition_cols:
        print(f"✓ Colunas de partição encontradas: {existing_partition_cols}")
        sql_query = f"""
            SELECT 
                {', '.join(df.columns)}
            FROM df_registered
            WHERE {' IS NOT NULL AND '.join(existing_partition_cols)} IS NOT NULL
        """
    
    df_transformed = conn.execute(sql_query).df()
    
    print(f"✓ Dados transformados")
    print(f"  Linhas originais: {len(df)}")
    print(f"  Linhas transformadas: {len(df_transformed)}")
    print(f"  Colunas: {list(df_transformed.columns)}")
    
    # Salvar dataframe transformado
    context['task_instance'].xcom_push(key='transformed_df', value=df_transformed)
    
    return {
        'status': 'success',
        'rows': len(df_transformed),
        'partition_columns': existing_partition_cols
    }


def insert_into_analytics_db(**context):
    """
    Insere dados transformados no banco analítico PostgreSQL
    """
    import os
    
    # Recuperar dataframe transformado
    df = context['task_instance'].xcom_pull(
        task_ids='transform_data',
        key='transformed_df'
    )
    
    # Configurações do PostgreSQL Analytics
    postgres_user = os.getenv('POSTGRES_ANALYTICS_USER', 'analytics_user')
    postgres_password = os.getenv('POSTGRES_ANALYTICS_PASSWORD', 'analytics_pass')
    postgres_host = os.getenv('POSTGRES_ANALYTICS_HOST', 'postgres-analytics')
    postgres_port = os.getenv('POSTGRES_ANALYTICS_PORT', '5432')
    postgres_db = os.getenv('POSTGRES_ANALYTICS_DB', 'analytics_db')
    
    try:
        # Criar string de conexão
        connection_string = (
            f"postgresql://{postgres_user}:{postgres_password}@"
            f"{postgres_host}:{postgres_port}/{postgres_db}"
        )
        
        # Criar engine SQLAlchemy
        engine = create_engine(connection_string)
        
        # Inserir dados na tabela fato_vendas
        # Nota: Ajuste nomes de colunas conforme necessário
        df_to_insert = df.rename(columns={
            'data': 'data_venda',
            'quantidade': 'quantidade',
            'valor_total': 'valor_total'
        })
        
        df_to_insert.to_sql(
            'fato_vendas',
            engine,
            schema='analytics',
            if_exists='append',
            index=False,
            method='multi',
            chunksize=1000
        )
        
        print(f"✓ Dados inseridos no banco analítico")
        print(f"  Tabela: analytics.fato_vendas")
        print(f"  Linhas inseridas: {len(df)}")
        
        engine.dispose()
        
        return {
            'status': 'success',
            'rows_inserted': len(df),
            'table': 'analytics.fato_vendas'
        }
        
    except Exception as e:
        print(f"✗ Erro ao inserir dados: {str(e)}")
        raise


# Tasks
task_read = PythonOperator(
    task_id='read_minio',
    python_callable=read_minio_with_duckdb,
    provide_context=True,
    dag=dag,
)

task_transform = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    provide_context=True,
    dag=dag,
)

task_insert = PythonOperator(
    task_id='insert_into_analytics',
    python_callable=insert_into_analytics_db,
    provide_context=True,
    dag=dag,
)

# Dependências
task_read >> task_transform >> task_insert
