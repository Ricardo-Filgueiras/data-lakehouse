"""
Script para gerar dados de teste e enviar para MinIO
Útil para testar o pipeline MinIO → DuckDB → PostgreSQL
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from minio import Minio
import io


def generate_sample_sales_data(num_records=1000):
    """Gera dados de vendas de exemplo em Parquet"""
    
    print("Gerando dados de vendas de exemplo...")
    
    # Gerar datas
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(days=x) for x in np.random.randint(0, 90, num_records)]
    
    # Dados de exemplo
    df = pd.DataFrame({
        'data': dates,
        'codigo_produto': np.random.choice([f'PROD{str(i).zfill(3)}' for i in range(1, 51)], num_records),
        'codigo_cliente': np.random.choice([f'CLI{str(i).zfill(4)}' for i in range(1, 101)], num_records),
        'quantidade': np.random.randint(1, 100, num_records),
        'valor_unitario': np.random.uniform(10, 1000, num_records),
    })
    
    # Calcular valor total
    df['valor_total'] = df['quantidade'] * df['valor_unitario']
    df['valor_total'] = df['valor_total'].round(2)
    
    # Remover coluna unitária
    df = df.drop('valor_unitario', axis=1)
    
    print(f"✓ {len(df)} registros gerados")
    print(f"\nAmostra dos dados:")
    print(df.head(10).to_string())
    
    return df


def upload_to_minio(df, bucket_name='bronze', file_name='vendas/vendas_sample.parquet'):
    """Envia dados Parquet para MinIO"""
    
    print(f"\nEnviando para MinIO...")
    
    try:
        # Conectar ao MinIO
        client = Minio(
            "minio:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False
        )
        
        # Verificar se bucket existe
        if not client.bucket_exists(bucket_name):
            print(f"Criando bucket '{bucket_name}'...")
            client.make_bucket(bucket_name)
        
        # Converter DataFrame para bytes Parquet
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        buffer.seek(0)
        
        # Upload para MinIO
        client.put_object(
            bucket_name,
            file_name,
            buffer,
            length=len(buffer.getvalue()),
            content_type='application/octet-stream'
        )
        
        print(f"✓ Arquivo enviado para s3://{bucket_name}/{file_name}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro ao enviar para MinIO: {str(e)}")
        print("  Dica: Certificar-se de que MinIO está rodando em minio:9000")
        return False


def upload_to_local_file(df, file_path='/tmp/vendas_sample.parquet'):
    """Salva dados localmente (útil se MinIO não estiver disponível)"""
    
    print(f"\nSalvando arquivo localmente...")
    
    try:
        df.to_parquet(file_path, index=False)
        print(f"✓ Arquivo salvo em: {file_path}")
        
        file_size_mb = len(df) * 50 / 1024 / 1024  # Aproximado
        print(f"  Tamanho: ~{file_size_mb:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro ao salvar: {str(e)}")
        return False


def generate_sample_csv(num_records=1000, file_path='/tmp/vendas_sample.csv'):
    """Gera dados em CSV em vez de Parquet"""
    
    print("Gerando dados em CSV...")
    
    df = generate_sample_sales_data(num_records)
    
    try:
        df.to_csv(file_path, index=False)
        print(f"✓ Arquivo CSV salvo em: {file_path}")
        return True
    except Exception as e:
        print(f"✗ Erro: {str(e)}")
        return False


def main():
    """Menu principal"""
    
    print("\n" + "="*60)
    print("GERADOR DE DADOS DE TESTE")
    print("MinIO → DuckDB → PostgreSQL")
    print("="*60)
    
    # Opções
    print("\nEscolha uma opção:")
    print("1. Gerar dados e enviar para MinIO (Parquet)")
    print("2. Gerar dados e salvar localmente (Parquet)")
    print("3. Gerar dados e salvar (CSV)")
    print("4. Sair")
    
    choice = input("\nOpção (1-4): ").strip()
    
    if choice == '1':
        df = generate_sample_sales_data(num_records=1000)
        upload_to_minio(df)
        
    elif choice == '2':
        df = generate_sample_sales_data(num_records=1000)
        upload_to_local_file(df)
        
    elif choice == '3':
        generate_sample_csv(num_records=1000)
        
    elif choice == '4':
        print("Saindo...")
        return
    
    else:
        print("Opção inválida")
        return
    
    print("\n" + "="*60)
    print("Próximo passo: Execute a DAG 'minio_to_analytics' no Airflow")
    print("="*60)


if __name__ == "__main__":
    # Você pode rodar direto ou usar o menu
    
    # Opção 1: Menu interativo
    # main()
    
    # Opção 2: Executar direto
    print("Se estiver rodando com MinIO disponível:")
    print(">>> python generate_test_data.py")
    
    print("\n--- Ou execute direto para testar ---")
    
    # Gerar dados localmente para teste
    df = generate_sample_sales_data(num_records=1000)
    upload_to_local_file(df)
