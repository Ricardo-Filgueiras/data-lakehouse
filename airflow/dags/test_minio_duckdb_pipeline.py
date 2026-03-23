"""
Script de teste para validar conexão MinIO ↔ DuckDB ↔ PostgreSQL
Útil para desenvolvimento e troubleshooting
"""

import duckdb
import pandas as pd
from sqlalchemy import create_engine
import os


def test_duckdb_minio_connection():
    """Testa leitura de dados do MinIO com DuckDB"""
    
    print("\n" + "="*60)
    print("TESTE 1: DuckDB + MinIO Connection")
    print("="*60)
    
    # Configurações
    minio_endpoint = os.getenv('MINIO_ENDPOINT', 'http://minio:9000')
    minio_access_key = os.getenv('MINIO_ROOT_USER', 'minioadmin')
    minio_secret_key = os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin')
    
    try:
        conn = duckdb.connect(':memory:')
        
        # Configurar credenciais S3/MinIO
        conn.execute(f"""
            SET secret (
                TYPE S3,
                PROVIDER credential_chain,
                KEY_ID '{minio_access_key}',
                SECRET '{minio_secret_key}',
                ENDPOINT '{minio_endpoint}',
                URL_STYLE 'path'
            );
        """)
        
        print("✓ Credenciais S3 configuradas")
        
        # Listar buckets (teste de conectividade)
        buckets = conn.execute("SELECT * FROM s3_scan('s3://*/');").fetchall()
        print(f"✓ Buckets encontrados: {len(buckets)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro: {str(e)}")
        return False


def test_duckdb_transformation():
    """Testa transformação de dados com DuckDB"""
    
    print("\n" + "="*60)
    print("TESTE 2: DuckDB SQL Transformation")
    print("="*60)
    
    try:
        # Criar dataframe de exemplo
        df_example = pd.DataFrame({
            'data': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'codigo_produto': ['PROD001', 'PROD002', 'PROD001'],
            'codigo_cliente': ['CLI001', 'CLI002', 'CLI001'],
            'quantidade': [10, 20, 15],
            'valor_total': [1000, 2000, 1500]
        })
        
        conn = duckdb.connect(':memory:')
        
        # Registrar dataframe
        conn.from_df(df_example)
        
        # Transformação SQL
        resultado = conn.execute("""
            SELECT 
                data,
                codigo_produto,
                codigo_cliente,
                quantidade,
                valor_total,
                CASE 
                    WHEN valor_total > 1500 THEN 'Alto'
                    ELSE 'Normal'
                END as categoria
            FROM df_example
            WHERE quantidade > 0
        """).df()
        
        print(f"✓ Transformação realizada")
        print(f"  Linhas: {len(resultado)}")
        print(f"  Colunas: {list(resultado.columns)}")
        print(f"\n{resultado.to_string()}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro: {str(e)}")
        return False


def test_postgres_connection():
    """Testa conexão com PostgreSQL Analytics"""
    
    print("\n" + "="*60)
    print("TESTE 3: PostgreSQL Analytics Connection")
    print("="*60)
    
    # Configurações
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
            result = conn.execute("SELECT 1 as test")
            conn.commit()
        
        print("✓ Conexão PostgreSQL estabelecida")
        
        # Verificar tabelas
        with engine.connect() as conn:
            tables = engine.table_names(schema='analytics')
            print(f"✓ Tabelas no schema 'analytics': {len(tables)}")
            for table in tables:
                print(f"  - {table}")
        
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"✗ Erro: {str(e)}")
        return False


def test_end_to_end():
    """Teste end-to-end: Cria, transforma e insere dados"""
    
    print("\n" + "="*60)
    print("TESTE 4: End-to-End (Create → Transform → Insert)")
    print("="*60)
    
    # Configurações PostgreSQL
    postgres_user = os.getenv('POSTGRES_ANALYTICS_USER', 'analytics_user')
    postgres_password = os.getenv('POSTGRES_ANALYTICS_PASSWORD', 'analytics_pass')
    postgres_host = os.getenv('POSTGRES_ANALYTICS_HOST', 'postgres-analytics')
    postgres_port = os.getenv('POSTGRES_ANALYTICS_PORT', '5432')
    postgres_db = os.getenv('POSTGRES_ANALYTICS_DB', 'analytics_db')
    
    try:
        # 1. Criar dados de exemplo
        df = pd.DataFrame({
            'data': ['2024-01-01', '2024-01-02'],
            'codigo_produto': ['PROD001', 'PROD002'],
            'codigo_cliente': ['CLI001', 'CLI002'],
            'quantidade': [10, 20],
            'valor_total': [1000, 2000]
        })
        
        print(f"✓ Dados de exemplo criados ({len(df)} linhas)")
        
        # 2. Transformar com DuckDB
        conn = duckdb.connect(':memory:')
        conn.from_df(df)
        
        df_transformed = conn.execute("""
            SELECT 
                CAST(data AS DATE) as data_venda,
                codigo_produto,
                codigo_cliente,
                quantidade,
                valor_total,
                0 as desconto
            FROM df
        """).df()
        
        print(f"✓ Dados transformados ({len(df_transformed)} linhas)")
        
        # 3. Inserir no PostgreSQL
        connection_string = (
            f"postgresql://{postgres_user}:{postgres_password}@"
            f"{postgres_host}:{postgres_port}/{postgres_db}"
        )
        
        engine = create_engine(connection_string)
        
        # Nota: Ajuste conforme suas colunas reais
        df_transformed.to_sql(
            'fato_vendas_teste',  # Usar tabela de teste
            engine,
            schema='analytics',
            if_exists='append',
            index=False,
            method='multi',
            chunksize=1000
        )
        
        print(f"✓ Dados inseridos na tabela analytics.fato_vendas_teste")
        
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"✗ Erro: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n" + "🧪 TESTES DE CONECTIVIDADE E PIPELINE")
    print("(Execute em um container Airflow ou localmente com .env configurado)")
    
    tests = [
        ("MinIO Connection", test_duckdb_minio_connection),
        ("DuckDB Transformation", test_duckdb_transformation),
        ("PostgreSQL Connection", test_postgres_connection),
        ("End-to-End Pipeline", test_end_to_end),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "PASSOU" if result else "FALHOU"))
        except Exception as e:
            print(f"\n✗ Exceção não tratada: {str(e)}")
            results.append((test_name, "ERRO"))
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    
    for test_name, status in results:
        emoji = "✓" if status == "PASSOU" else "✗"
        print(f"{emoji} {test_name}: {status}")
    
    print("="*60)
