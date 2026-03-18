# MinIO - Serviço Independente

Este diretório contém a configuração completa do **MinIO** como um serviço independente e reutilizável.

## 📦 O que é MinIO?

MinIO é um servidor S3-compatível de código aberto que permite armazenar objetos. Ideal para:
- Data Lakes
- Backup de dados
- Armazenamento de arquivos temporários
- Testes com S3-like storage

## 🚀 Como Usar

### Executar MinIO

```bash
# Do diretório raiz do projeto
docker compose -f minio/docker-compose.yml up -d

# Ou de dentro da pasta minio
cd minio
docker compose up -d
```

### Parar MinIO

```bash
docker compose -f minio/docker-compose.yml down

# Se quiser remover dados persistentes
docker compose -f minio/docker-compose.yml down -v
```

## 🔗 Acessos

- **MinIO API**: `http://localhost:9000`
- **MinIO Console (UI)**: `http://localhost:9001`
- **Credenciais**: Use `MINIO_ROOT_USER` e `MINIO_ROOT_PASSWORD` do `.env`

## 📊 Buckets Criados Automaticamente

Ao iniciar, os seguintes buckets são criados:
- `landing` - Dados brutos ingestados
- `bronze` - Zona Bronze (dados validados)
- `silver` - Zona Silver (dados processados)
- `gold` - Zona Gold (dados finais)

## 🔌 Integrando MinIO com Trino

Se quiser usar MinIO como storage backend para Trino:

```properties
# No arquivo conf/delta.properties (ou outro catalogador)
s3_endpoint=http://minio:9000
s3_access_key=${AWS_ACCESS_KEY_ID}
s3_secret_key=${AWS_SECRET_ACCESS_KEY}
s3_path_style_access=true
s3_region=us-east-1
```

## 🌐 Rede Compartilhada

MinIO utiliza a rede `trino` para comunicação:
- Dentro de containers Docker: `http://minio:9000`
- Do host (máquina local): `http://localhost:9000`

## 💾 Dados Persistentes

MinIO usa um volume chamado `minio` para todos os dados:
```yaml
volumes:
  - minio:/data
```

Para limpar todos os dados, execute:
```bash
docker volume rm minio
```

## 🛠️ Troubleshooting

**MinIO não inicia?**
```bash
docker compose -f minio/docker-compose.yml logs minio
```

**Verificar se está saudável:**
```bash
curl -f http://localhost:9000/minio/health/live
```

**Resetar tudo:**
```bash
docker compose -f minio/docker-compose.yml down -v
docker compose -f minio/docker-compose.yml up -d
```

## 📄 Variáveis de Ambiente Necessárias

Certifique-se que seu `.env` contém:

```env
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
```

## 📝 Arquitetura

```
MinIO Service
├── API Server (porta 9000)
├── Console (porta 9001)
└── Storage Volume (minio:/data)
    ├── landing/
    ├── bronze/
    ├── silver/
    └── gold/
```

## 🔄 Reutilizar em Outros Projetos

Para usar MinIO em outro projeto, copie apenas este diretório:

```bash
cp -r minio ../outro-projeto/
cd ../outro-projeto
docker compose -f minio/docker-compose.yml up -d
```

Certifique-se de que o `.env` está disponível no projeto.

---

**Nota**: MinIO é totalmente **independente** do Trino. Pode ser executado com ou sem Trino.
