"""
Script standalone para testar conexão com PostgreSQL Analytics
Pode ser executado localmente ou dentro do container Airflow
"""

import psycopg2
from sqlalchemy import create_engine, text
import pandas as pd
import os
import sys


def test_postgres_connection():
    """Testa conexão básica com PostgreSQL"""
    print("\n" + "="*60)
    print("TESTE 1: Conexão PostgreSQL")
    print("="*60)

    # Configurações
    postgres_user = os.getenv('POSTGRES_ANALYTICS_USER', 'analytics_user')
    postgres_password = os.getenv('POSTGRES_ANALYTICS_PASSWORD', 'analytics_pass')
    postgres_host = os.getenv('POSTGRES_ANALYTICS_HOST', 'postgres-analytics')
    postgres_port = os.getenv('POSTGRES_ANALYTICS_PORT', '5432')
    postgres_db = os.getenv('POSTGRES_ANALYTICS_DB', 'analytics_db')

    try:
        print(f"Conectando a: {postgres_host}:{postgres_port}/{postgres_db}")

        conn = psycopg2.connect(
            host=postgres_host,
            port=postgres_port,
            database=postgres_db,
            user=postgres_user,
            password=postgres_password,
            connect_timeout=10
        )

        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]

        cur.close()
        conn.close()

        print("✅ Conexão estabelecida com sucesso!")
        print(f"   PostgreSQL Version: {version[:80]}...")

        return True

    except Exception as e:
        print(f"❌ Erro na conexão: {str(e)}")
        return False


def test_analytics_schema():
    """Testa schema e tabelas"""
    print("\n" + "="*60)
    print("TESTE 2: Schema Analytics")
    print("="*60)

    postgres_user = os.getenv('POSTGRES_ANALYTICS_USER', 'analytics_user')
    postgres_password = os.getenv('POSTGRES_ANALYTICS_PASSWORD', 'analytics_pass')
    postgres_host = os.getenv('POSTGRES_ANALYTICS_HOST', 'postgres-analytics')
    postgres_port = os.getenv('POSTGRES_ANALYTICS_PORT', '5432')
    postgres_db = os.getenv('POSTGRES_ANALYTICS_DB', 'analytics_db')

    try:
        connection_string = (
            f"postgresql://{postgres_user}:{postgres_password}@"
            f"{postgres_host}:{postgres_port}/{postgres_db}"
        )

        engine = create_engine(connection_string)

        with engine.connect() as conn:
            # Verificar schema
            result = conn.execute(text("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = 'analytics'
            """))

            if result.fetchone():
                print("✅ Schema 'analytics' encontrado")
            else:
                print("❌ Schema 'analytics' não encontrado")
                return False

            # Listar tabelas
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'analytics'
                ORDER BY table_name
            """))

            tables = [row[0] for row in result.fetchall()]
            expected_tables = ['dim_tempo', 'dim_produto', 'dim_cliente', 'fato_vendas']

            print(f"📊 Tabelas encontradas: {tables}")
            print(f"🎯 Tabelas esperadas: {expected_tables}")

            missing = [t for t in expected_tables if t not in tables]
            if missing:
                print(f"⚠️ Tabelas faltando: {missing}")
                return False
            else:
                print("✅ Todas as tabelas do star schema encontradas")
                return True

    except Exception as e:
        print(f"❌ Erro ao verificar schema: {str(e)}")
        return False


def test_data_operations():
    """Testa operações CRUD"""
    print("\n" + "="*60)
    print("TESTE 3: Operações de Dados")
    print("="*60)

    postgres_user = os.getenv('POSTGRES_ANALYTICS_USER', 'analytics_user')
    postgres_password = os.getenv('POSTGRES_ANALYTICS_PASSWORD', 'analytics_pass')
    postgres_host = os.getenv('POSTGRES_ANALYTICS_HOST', 'postgres-analytics')
    postgres_port = os.getenv('POSTGRES_ANALYTICS_PORT', '5432')
    postgres_db = os.getenv('POSTGRES_ANALYTICS_DB', 'analytics_db')

    try:
        connection_string = (
            f"postgresql://{postgres_user}:{postgres_password}@"
            f"{postgres_host}:{postgres_port}/{postgres_db}"
        )

        engine = create_engine(connection_string)

        with engine.connect() as conn:
            print("🔄 Testando operações CRUD...")

            # 1. INSERT
            print("   1. INSERT...")
            conn.execute(text("""
                INSERT INTO analytics.dim_tempo (
                    data, ano, mes, dia, trimestre, dia_semana, nome_mes, nome_dia_semana
                ) VALUES (
                    '2024-12-25'::DATE, 2024, 12, 25, 4, 3, 'December', 'Wednesday'
                )
                ON CONFLICT (data) DO NOTHING
            """))
            conn.commit()
            print("      ✅ INSERT executado")

            # 2. SELECT
            print("   2. SELECT...")
            result = conn.execute(text("SELECT COUNT(*) FROM analytics.dim_tempo"))
            count = result.fetchone()[0]
            print(f"      ✅ SELECT: {count} registros na dim_tempo")

            # 3. UPDATE
            print("   3. UPDATE...")
            conn.execute(text("""
                UPDATE analytics.dim_tempo
                SET nome_mes = 'Dezembro'
                WHERE data = '2024-12-25'::DATE
            """))
            conn.commit()
            print("      ✅ UPDATE executado")

            # 4. Verificar UPDATE
            result = conn.execute(text("""
                SELECT nome_mes FROM analytics.dim_tempo
                WHERE data = '2024-12-25'::DATE
            """))
            nome_mes = result.fetchone()
            if nome_mes:
                print(f"      ✅ UPDATE verificado: nome_mes = '{nome_mes[0]}'")

            # 5. DELETE (limpar teste)
            print("   4. DELETE (limpeza)...")
            conn.execute(text("""
                DELETE FROM analytics.dim_tempo
                WHERE data = '2024-12-25'::DATE
            """))
            conn.commit()
            print("      ✅ DELETE executado")

            print("✅ Todas as operações CRUD executadas com sucesso!")
            return True

    except Exception as e:
        print(f"❌ Erro nas operações: {str(e)}")
        return False


def test_trino_connectivity():
    """Testa conectividade básica com Trino"""
    print("\n" + "="*60)
    print("TESTE 4: Conectividade Trino")
    print("="*60)

    try:
        import requests

        trino_host = os.getenv('TRINO_HOST', 'trino')
        trino_port = os.getenv('TRINO_PORT', '8080')
        trino_url = f"http://{trino_host}:{trino_port}/v1/info"

        print(f"Testando Trino em: {trino_url}")

        response = requests.get(trino_url, timeout=10)

        if response.status_code == 200:
            info = response.json()
            print("✅ Trino está respondendo!")
            print(f"   Node Version: {info.get('nodeVersion', {}).get('version', 'unknown')}")
            print(f"   Environment: {info.get('environment', 'unknown')}")
            return True
        else:
            print(f"⚠️ Trino respondeu com status: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erro de conectividade com Trino: {str(e)}")
        print("   Nota: Trino pode não estar rodando ou rede pode estar bloqueada")
        return False
    except Exception as e:
        print(f"⚠️ Erro geral: {str(e)}")
        return False


def main():
    """Executa todos os testes"""
    print("🧪 TESTE STANDALONE - CONEXÃO ANALYTICS")
    print("Executando testes fora do Airflow...")

    # Verificar variáveis de ambiente
    print("\n📋 Variáveis de Ambiente:")
    env_vars = [
        'POSTGRES_ANALYTICS_HOST',
        'POSTGRES_ANALYTICS_PORT',
        'POSTGRES_ANALYTICS_USER',
        'POSTGRES_ANALYTICS_DB'
    ]

    for var in env_vars:
        value = os.getenv(var, f'[não definido - usando default]')
        print(f"   {var}: {value}")

    # Executar testes
    tests = [
        ("Conexão PostgreSQL", test_postgres_connection),
        ("Schema Analytics", test_analytics_schema),
        ("Operações CRUD", test_data_operations),
        ("Conectividade Trino", test_trino_connectivity),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "PASSOU" if result else "FALHOU"))
        except Exception as e:
            print(f"❌ Exceção não tratada em {test_name}: {str(e)}")
            results.append((test_name, "ERRO"))

    # Relatório final
    print("\n" + "="*60)
    print("RELATÓRIO FINAL")
    print("="*60)

    passed = 0
    for test_name, status in results:
        emoji = "✅" if status == "PASSOU" else "❌"
        print(f"{emoji} {test_name}: {status}")
        if status == "PASSOU":
            passed += 1

    print("="*60)
    print(f"📊 Resultado: {passed}/{len(results)} testes passaram")

    if passed == len(results):
        print("🎉 Todos os testes passaram! Banco analítico está saudável.")
        return 0
    else:
        print("⚠️ Alguns testes falharam. Verifique os logs acima.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)