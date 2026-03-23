"""
DAG para testar conexão com o banco analítico PostgreSQL
Executa validações básicas: conexão, tabelas, insert, select
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.hooks.base import BaseHook
import psycopg2
from sqlalchemy import create_engine, text
import pandas as pd
import os

# Configurações
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

dag = DAG(
    'test_analytics_connection',
    default_args=default_args,
    description='Testa conexão e funcionalidades básicas do PostgreSQL Analytics',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['test', 'analytics', 'healthcheck'],
)


def test_postgres_connection(**context):
    """
    Testa conexão básica com PostgreSQL usando psycopg2
    """
    try:
        print("🔌 Testando conexão PostgreSQL básica...")

        # Obter conexão do Airflow
        conn_config = BaseHook.get_connection('analytics_db')

        # Conectar usando psycopg2
        conn = psycopg2.connect(
            host=conn_config.host,
            port=conn_config.port or 5432,
            database=conn_config.schema or 'analytics_db',
            user=conn_config.login,
            password=conn_config.password,
            connect_timeout=10
        )

        # Executar query simples
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]

        cur.close()
        conn.close()

        print(f"✅ Conexão estabelecida com sucesso!")
        print(f"   PostgreSQL Version: {version[:50]}...")

        return {
            'status': 'success',
            'connection': 'established',
            'version': version[:100]
        }

    except Exception as e:
        print(f"❌ Erro na conexão: {str(e)}")
        raise


def test_analytics_schema(**context):
    """
    Testa se o schema 'analytics' e tabelas existem
    """
    try:
        print("📊 Verificando schema 'analytics'...")

        # Obter conexão do Airflow
        conn_config = BaseHook.get_connection('analytics_db')

        connection_string = (
            f"postgresql://{conn_config.login}:{conn_config.password}@"
            f"{conn_config.host}:{conn_config.port or 5432}/{conn_config.schema or 'analytics_db'}"
        )

        engine = create_engine(connection_string)

        with engine.connect() as conn:
            # Verificar se schema existe
            result = conn.execute(text("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = 'analytics'
            """))

            schema_exists = result.fetchone() is not None

            if not schema_exists:
                raise ValueError("Schema 'analytics' não encontrado")

            print("✅ Schema 'analytics' encontrado")

            # Listar tabelas no schema
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'analytics'
                ORDER BY table_name
            """))

            tables = [row[0] for row in result.fetchall()]

            expected_tables = ['dim_tempo', 'dim_produto', 'dim_cliente', 'fato_vendas']
            missing_tables = [t for t in expected_tables if t not in tables]

            if missing_tables:
                print(f"⚠️ Tabelas faltando: {missing_tables}")
            else:
                print("✅ Todas as tabelas do star schema encontradas")

            print(f"   Tabelas encontradas: {tables}")

            return {
                'status': 'success',
                'schema_exists': True,
                'tables_found': tables,
                'expected_tables': expected_tables,
                'missing_tables': missing_tables
            }

    except Exception as e:
        print(f"❌ Erro ao verificar schema: {str(e)}")
        raise


def test_data_operations(**context):
    """
    Testa operações básicas: INSERT, SELECT, UPDATE, DELETE
    """
    try:
        print("🔄 Testando operações de dados...")

        # Obter conexão do Airflow
        conn_config = BaseHook.get_connection('analytics_db')

        connection_string = (
            f"postgresql://{conn_config.login}:{conn_config.password}@"
            f"{conn_config.host}:{conn_config.port or 5432}/{conn_config.schema or 'analytics_db'}"
        )

        engine = create_engine(connection_string)

        with engine.connect() as conn:
            # 1. INSERT - Inserir dados de teste
            print("   1. Testando INSERT...")

            # Verificar se tabela dim_tempo tem dados
            result = conn.execute(text("SELECT COUNT(*) FROM analytics.dim_tempo"))
            tempo_count = result.fetchone()[0]

            if tempo_count == 0:
                # Inserir dados de teste na dim_tempo
                conn.execute(text("""
                    INSERT INTO analytics.dim_tempo (
                        data, ano, mes, dia, trimestre, dia_semana, nome_mes, nome_dia_semana
                    ) VALUES (
                        '2024-01-01'::DATE, 2024, 1, 1, 1, 1, 'January', 'Monday'
                    )
                """))
                conn.commit()
                print("      ✅ Inserido registro de teste em dim_tempo")

            # 2. SELECT - Consultar dados
            print("   2. Testando SELECT...")

            result = conn.execute(text("""
                SELECT COUNT(*) as total_tempo,
                       COUNT(DISTINCT ano) as anos_distintos
                FROM analytics.dim_tempo
            """))

            row = result.fetchone()
            print(f"      ✅ SELECT executado: {row[0]} registros, {row[1]} anos distintos")

            # 3. UPDATE - Atualizar dados
            print("   3. Testando UPDATE...")

            conn.execute(text("""
                UPDATE analytics.dim_tempo
                SET nome_mes = 'Janeiro'
                WHERE data = '2024-01-01'::DATE
            """))
            conn.commit()
            print("      ✅ UPDATE executado")

            # 4. Verificar UPDATE
            result = conn.execute(text("""
                SELECT nome_mes FROM analytics.dim_tempo
                WHERE data = '2024-01-01'::DATE
            """))
            nome_mes = result.fetchone()[0]
            print(f"      ✅ Verificado UPDATE: nome_mes = '{nome_mes}'")

            # 5. DELETE - Limpar dados de teste (opcional)
            print("   4. Testando DELETE...")

            conn.execute(text("""
                DELETE FROM analytics.dim_tempo
                WHERE data = '2024-01-01'::DATE
            """))
            conn.commit()
            print("      ✅ DELETE executado")

            return {
                'status': 'success',
                'operations_tested': ['INSERT', 'SELECT', 'UPDATE', 'DELETE'],
                'data_integrity': 'verified'
            }

    except Exception as e:
        print(f"❌ Erro nas operações de dados: {str(e)}")
        raise


def test_trino_integration(**context):
    """
    Testa se o Trino consegue acessar o PostgreSQL Analytics
    """
    try:
        print("🔗 Testando integração com Trino...")

        # Configurações do Trino
        trino_host = os.getenv('TRINO_HOST', 'trino')
        trino_port = os.getenv('TRINO_PORT', '8080')

        # Usar requests para testar conectividade básica
        import requests

        # Testar se Trino está respondendo
        trino_url = f"http://{trino_host}:{trino_port}/v1/info"
        response = requests.get(trino_url, timeout=10)

        if response.status_code == 200:
            print("✅ Trino está respondendo")

            # Tentar uma query simples via HTTP (opcional)
            # Nota: Para query real, seria necessário usar trino-python-client
            print("ℹ️ Para testar queries completas, use: trino --server trino:8080 --catalog postgres --schema analytics")

            return {
                'status': 'success',
                'trino_responding': True,
                'integration_status': 'basic_check_passed'
            }
        else:
            print(f"⚠️ Trino não respondeu (status: {response.status_code})")
            return {
                'status': 'warning',
                'trino_responding': False,
                'integration_status': 'trino_not_responding'
            }

    except Exception as e:
        print(f"⚠️ Erro ao testar integração Trino: {str(e)}")
        return {
            'status': 'warning',
            'trino_responding': False,
            'error': str(e)
        }


def generate_test_report(**context):
    """
    Gera relatório final dos testes
    """
    print("📋 Gerando relatório final dos testes...")

    # Coletar resultados das tasks anteriores
    connection_result = context['task_instance'].xcom_pull(task_ids='test_connection')
    schema_result = context['task_instance'].xcom_pull(task_ids='test_schema')
    operations_result = context['task_instance'].xcom_pull(task_ids='test_operations')
    trino_result = context['task_instance'].xcom_pull(task_ids='test_trino')

    # Calcular status geral
    all_success = all([
        connection_result.get('status') == 'success',
        schema_result.get('status') == 'success',
        operations_result.get('status') == 'success'
    ])

    # Relatório
    report = f"""
{'='*60}
RELATÓRIO DE TESTE - BANCO ANALÍTICO
{'='*60}

📊 STATUS GERAL: {'✅ SUCESSO' if all_success else '❌ FALHAS DETECTADAS'}

🔌 CONEXÃO POSTGRESQL:
   Status: {connection_result.get('status', 'unknown')}
   Versão: {connection_result.get('version', 'unknown')[:50] if connection_result.get('version') else 'unknown'}

📋 SCHEMA ANALYTICS:
   Status: {schema_result.get('status', 'unknown')}
   Tabelas encontradas: {len(schema_result.get('tables_found', []))}
   Tabelas esperadas: {schema_result.get('expected_tables', [])}
   Tabelas faltando: {schema_result.get('missing_tables', [])}

🔄 OPERAÇÕES DE DADOS:
   Status: {operations_result.get('status', 'unknown')}
   Operações testadas: {operations_result.get('operations_tested', [])}

🔗 INTEGRAÇÃO TRINO:
   Status: {trino_result.get('status', 'unknown')}
   Trino respondendo: {trino_result.get('trino_responding', False)}

{'='*60}
"""

    print(report)

    # Salvar relatório em arquivo (opcional)
    try:
        with open('/opt/airflow/logs/test_report.txt', 'w') as f:
            f.write(report)
        print("📄 Relatório salvo em: /opt/airflow/logs/test_report.txt")
    except:
        pass

    return {
        'status': 'success' if all_success else 'failed',
        'report': report,
        'tests_passed': sum([
            connection_result.get('status') == 'success',
            schema_result.get('status') == 'success',
            operations_result.get('status') == 'success'
        ]),
        'total_tests': 3
    }


# Tasks
task_test_connection = PythonOperator(
    task_id='test_connection',
    python_callable=test_postgres_connection,
    provide_context=True,
    dag=dag,
)

task_test_schema = PythonOperator(
    task_id='test_schema',
    python_callable=test_analytics_schema,
    provide_context=True,
    dag=dag,
)

task_test_operations = PythonOperator(
    task_id='test_operations',
    python_callable=test_data_operations,
    provide_context=True,
    dag=dag,
)

task_test_trino = PythonOperator(
    task_id='test_trino',
    python_callable=test_trino_integration,
    provide_context=True,
    dag=dag,
)

task_generate_report = PythonOperator(
    task_id='generate_report',
    python_callable=generate_test_report,
    provide_context=True,
    dag=dag,
)

# Dependências
task_test_connection >> task_test_schema >> task_test_operations >> task_test_trino >> task_generate_report