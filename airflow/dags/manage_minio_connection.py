"""
Script para gerenciar o conector 'mini_defalt' no Airflow 3.0.6
Execute dentro do container Airflow ou com acesso ao banco de dados Django
"""

from airflow.models import Connection
from airflow import settings
from sqlalchemy.orm import sessionmaker


def check_minio_connection(conn_id='mini_defalt'):
    """Verifica se o conector MinIO existe"""
    
    print(f"\n{'='*60}")
    print(f"Verificando conector: {conn_id}")
    print('='*60)
    
    try:
        from airflow.hooks.base import BaseHook
        conn = BaseHook.get_connection(conn_id)
        
        if conn:
            print(f"✓ Conector '{conn_id}' encontrado!")
            print(f"  Tipo: {conn.conn_type}")
            print(f"  Host: {conn.host}")
            print(f"  Login: {conn.login}")
            print(f"  Port: {conn.port}")
            
            if conn.extra:
                print(f"  Extra: {conn.extra}")
            
            return True
        else:
            print(f"✗ Conector '{conn_id}' não encontrado")
            return False
            
    except Exception as e:
        print(f"✗ Erro ao verificar: {str(e)}")
        return False


def create_minio_connection(
    conn_id='mini_defalt',
    conn_type='aws',
    host='minio:9000',
    login='minioadmin',
    password='minioadmin',
    extra_json=None
):
    """Cria conector MinIO no Airflow"""
    
    print(f"\n{'='*60}")
    print(f"Criando conector: {conn_id}")
    print('='*60)
    
    if extra_json is None:
        extra_json = '{"host": "http://minio:9000"}'
    
    try:
        # Criar conexão
        conn = Connection(
            conn_id=conn_id,
            conn_type=conn_type,
            host=host,
            login=login,
            password=password,
            extra=extra_json
        )
        
        # Salvar no banco de dados
        Session = sessionmaker(bind=settings.engine)
        session = Session()
        
        # Verificar se já existe
        existing = session.query(Connection).filter(
            Connection.conn_id == conn_id
        ).first()
        
        if existing:
            print(f"⚠ Conector '{conn_id}' já existe. Atualizando...")
            existing.conn_type = conn.conn_type
            existing.host = conn.host
            existing.login = conn.login
            existing.password = conn.password
            existing.extra = conn.extra
            session.commit()
        else:
            print(f"Criando novo conector...")
            session.add(conn)
            session.commit()
        
        session.close()
        
        print(f"✓ Conector '{conn_id}' criado/atualizado com sucesso!")
        print(f"  Tipo: {conn_type}")
        print(f"  Host: {host}")
        print(f"  Login: {login}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro ao criar conector: {str(e)}")
        return False


def delete_minio_connection(conn_id='mini_defalt'):
    """Deleta conector MinIO"""
    
    print(f"\n{'='*60}")
    print(f"Deletando conector: {conn_id}")
    print('='*60)
    
    try:
        Session = sessionmaker(bind=settings.engine)
        session = Session()
        
        conn = session.query(Connection).filter(
            Connection.conn_id == conn_id
        ).first()
        
        if conn:
            session.delete(conn)
            session.commit()
            print(f"✓ Conector '{conn_id}' deletado com sucesso!")
        else:
            print(f"✗ Conector '{conn_id}' não encontrado")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"✗ Erro ao deletar: {str(e)}")
        return False


def list_all_connections(filter_type='aws'):
    """Lista todas as conexões (filtrado por tipo)"""
    
    print(f"\n{'='*60}")
    print(f"Listando conexões (tipo: {filter_type})")
    print('='*60)
    
    try:
        Session = sessionmaker(bind=settings.engine)
        session = Session()
        
        if filter_type:
            connections = session.query(Connection).filter(
                Connection.conn_type == filter_type
            ).all()
        else:
            connections = session.query(Connection).all()
        
        if connections:
            for conn in connections:
                print(f"\n  ID: {conn.conn_id}")
                print(f"  Tipo: {conn.conn_type}")
                print(f"  Host: {conn.host}")
                print(f"  Login: {conn.login}")
        else:
            print(f"Nenhuma conexão encontrada (tipo: {filter_type})")
        
        session.close()
        
    except Exception as e:
        print(f"✗ Erro ao listar: {str(e)}")


def test_minio_hook(conn_id='mini_defalt', bucket='teste01'):
    """Testa o S3Hook com o conector MinIO"""
    
    print(f"\n{'='*60}")
    print(f"Testando S3Hook com conector: {conn_id}")
    print('='*60)
    
    try:
        from airflow.providers.amazon.aws.hooks.s3 import S3Hook
        
        hook = S3Hook(aws_conn_id=conn_id)
        
        print(f"✓ S3Hook criado com sucesso")
        
        # Tentar listar buckets
        print(f"\nTentando listar arquivos no bucket: {bucket}")
        
        files = hook.list_keys(bucket_name=bucket)
        
        print(f"✓ Conexão com MinIO via S3Hook funcionando!")
        
        if files:
            print(f"✓ {len(files)} arquivo(s) encontrado(s):")
            for file in files[:10]:  # Mostrar primeiros 10
                print(f"    - {file}")
            if len(files) > 10:
                print(f"    ... e mais {len(files) - 10}")
        else:
            print("⚠ Nenhum arquivo encontrado no bucket")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro ao testar S3Hook: {str(e)}")
        return False


def main():
    """Menu principal"""
    
    print("\n" + "="*60)
    print("GERENCIADOR DE CONECTOR MINIO NO AIRFLOW")
    print("="*60)
    
    while True:
        print("\nOpções:")
        print("1. Verificar conector 'mini_defalt'")
        print("2. Criar/Atualizar conector 'mini_defalt'")
        print("3. Deletar conector")
        print("4. Listar todas as conexões AWS/S3")
        print("5. Testar S3Hook com o conector")
        print("6. Sair")
        
        choice = input("\nEscolha (1-6): ").strip()
        
        if choice == '1':
            check_minio_connection()
            
        elif choice == '2':
            create_minio_connection(
                conn_id='mini_defalt',
                conn_type='aws',
                host='minio:9000',
                login='minioadmin',
                password='minioadmin'
            )
            
        elif choice == '3':
            delete_minio_connection()
            
        elif choice == '4':
            list_all_connections(filter_type='aws')
            
        elif choice == '5':
            test_minio_hook(conn_id='mini_defalt', bucket='teste01')
            
        elif choice == '6':
            print("\nSaindo...")
            break
        
        else:
            print("Opção inválida")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Executar comando direto
        command = sys.argv[1]
        
        if command == 'check':
            check_minio_connection()
        elif command == 'create':
            create_minio_connection()
        elif command == 'delete':
            delete_minio_connection()
        elif command == 'list':
            list_all_connections()
        elif command == 'test':
            test_minio_hook()
        else:
            print(f"Comando desconhecido: {command}")
    else:
        # Menu interativo
        main()
