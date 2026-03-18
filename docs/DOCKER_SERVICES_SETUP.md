# Arquitetura dos Serviços: Trino + MinIO

O projeto está organizado em **stacks separados** para melhor modularidade e reutilização:

## 📁 Estrutura de Pastas

```
project/
├── docker-compose.yml              # Trino + Metastore Hive
├── conf/                           # Configs Trino
│   ├── config.properties
│   ├── delta.properties
│   ├── hive.properties
│   ├── iceberg.properties
│   ├── postgres.properties
│   └── sqlserver.properties
├── metastore/                      # Configs Hive Metastore
│   ├── core-site.xml
│   └── metastore-site.xml
├── minio/                          # Stack MinIO (independente)
│   ├── docker-compose.yml
│   ├── README.md
│   └── ...
└── DOCKER_SERVICES_SETUP.md        # Este arquivo
```

## 🎯 Cada Stack

### 1️⃣ **Trino + Hive Metastore** (`docker-compose.yml`)

Serviços:
- `trino` - Query engine
- `metastore-db` - MariaDB para Metastore
- `create-metastore-schema` - Inicializa schema
- `metastore` - Hive Metastore (catálogo)

**Iniciar:**
```bash
docker compose up -d
```

**Acessar:**
- Trino: `https://localhost:8443`

---

### 2️⃣ **MinIO** (`minio/docker-compose.yml`)

Serviços:
- `minio` - S3-compatible object storage
- `createbucket` - Cria buckets automaticamente (landing, bronze, silver, gold)

**Iniciar:**
```bash
docker compose -f minio/docker-compose.yml up -d
```

**Acessar:**
- MinIO API: `http://localhost:9000`
- MinIO Console: `http://localhost:9001`

**Documentação:** Ver [minio/README.md](minio/README.md)

---

## 🚀 Cenários de Uso

### Cenário 1: Apenas Trino (sem MinIO)

```bash
docker compose up -d
```

Trino roda com Metastore local. Ideal para consultas sem storage S3.

---

### Cenário 2: Apenas MinIO (sem Trino)

```bash
docker compose -f minio/docker-compose.yml up -d
```

MinIO roda de forma independente. Reutilizável em outros projetos.

---

### Cenário 3: Trino + MinIO (Stack Completo)

```bash
# Opção 1: Executar sequencialmente
docker compose -f minio/docker-compose.yml up -d
docker compose up -d

# Opção 2: Executar ambos de uma vez
docker compose -f minio/docker-compose.yml -f docker-compose.yml up -d
```

Trino acessa MinIO via `http://minio:9000` (rede Docker compartilhada).

---

## 🌐 Rede Compartilhada

Ambos os stacks usam a rede `trino` explícita:

```yaml
networks:
  trino:
    driver: bridge
    name: trino
```

Isso garante:
- ✅ Comunicação entre containers: `http://minio:9000` (do Trino)
- ✅ Ambos podem rodar juntos
- ✅ Mesmo stack em múltiplos projetos

---

## 📋 Variáveis de Ambiente Necessárias

Crie `.env` na raiz:

```env
# Trino / Metastore
MYSQL_ROOT_PASSWORD=root_password
MYSQL_ROOT_USER=root

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# AWS/S3 (para Hive Metastore com MinIO)
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
```

---

## 🔌 Integrar MinIO com Trino

Para usar MinIO como storage backend:

### Opção 1: Delta Lake (`conf/delta.properties`)

```properties
connector.name=delta
hive.metastore.uri=thrift://metastore:9083
s3_endpoint=http://minio:9000
s3_access_key=${AWS_ACCESS_KEY_ID}
s3_secret_key=${AWS_SECRET_ACCESS_KEY}
s3_path_style_access=true
s3_region=us-east-1
```

### Opção 2: Hive (`conf/hive.properties`)

```properties
connector.name=hive
hive.metastore.uri=thrift://metastore:9083
hive.s3.endpoint=http://minio:9000
hive.s3.aws-access-key=${AWS_ACCESS_KEY_ID}
hive.s3.aws-secret-key=${AWS_SECRET_ACCESS_KEY}
hive.s3.path-style-access=true
hive.s3.region=us-east-1
```

---

## 🛑 Parar Serviços

```bash
# Parar Trino apenas
docker compose down

# Parar MinIO apenas
docker compose -f minio/docker-compose.yml down

# Parar ambos
docker compose -f minio/docker-compose.yml -f docker-compose.yml down

# Parar e limpar volumes (CUIDADO: deleta dados!)
docker compose -f minio/docker-compose.yml -f docker-compose.yml down -v
```

---

## 🔄 Reutilizar MinIO em Outro Projeto

MinIO é totalmente independente. Para usar em outro projeto:

```bash
# Copiar pasta minio
cp -r minio /path/to/outro-projeto/

# Entrar no outro projeto
cd /path/to/outro-projeto

# Executar
docker compose -f minio/docker-compose.yml up -d
```

Certifique-se de que `.env` existe no novo projeto com credenciais MinIO.

---

## 📊 Verificar Status

```bash
# Listar containers
docker compose ps
docker compose -f minio/docker-compose.yml ps

# Ver logs
docker compose logs -f trino
docker compose -f minio/docker-compose.yml logs -f minio

# Verificar rede
docker network inspect trino
```

---

## 🐛 Troubleshooting

### MinIO não conecta com Trino?

```bash
# Verificar rede
docker network inspect trino

# Testar conectividade do Trino para MinIO
docker exec trino curl -v http://minio:9000

# Se não funcionar, reiniciar ambos
docker compose -f minio/docker-compose.yml down
docker compose down
docker compose -f minio/docker-compose.yml up -d
docker compose up -d
```

### Erro de permissão MinIO?

```bash
# Verificar credenciais no .env
cat .env | grep MINIO

# Resetar MinIO
docker compose -f minio/docker-compose.yml down -v
docker compose -f minio/docker-compose.yml up -d
```

### Trino não encontra Metastore?

```bash
# Verificar se Metastore está saudável
docker compose logs metastore

# Reiniciar Metastore
docker compose restart metastore
```

---

## 📚 Referências

- **Trino**: https://trino.io/docs/
- **MinIO**: https://min.io/docs/
- **Hive Metastore**: https://cwiki.apache.org/confluence/display/Hive/Design
