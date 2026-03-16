#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)

echo "[1/5] Verificando arquivos de configuração..."
for f in "$ROOT_DIR/.env" "$ROOT_DIR/airflow/.env" "$ROOT_DIR/trino/.env"; do
  if [[ ! -f "$f" ]]; then
    echo "ERRO: arquivo $f não encontrado. Copie .env.example e ajuste as variáveis." >&2
    exit 1
  fi
done

cp "$ROOT_DIR/.env" "$ROOT_DIR/trino/.env"
cp "$ROOT_DIR/.env" "$ROOT_DIR/metastore/.env"
cp "$ROOT_DIR/.env" "$ROOT_DIR/minio/.env"
cp "$ROOT_DIR/.env" "$ROOT_DIR/airflow/.env"

echo "[2/5] Criando rede Docker src_lakehouse (se não existir)..."
docker network inspect src_lakehouse >/dev/null 2>&1 || docker network create src_lakehouse

echo "[3/5] Iniciando MinIO..."
docker compose -f "$ROOT_DIR/minio/docker-compose.yml" up -d

echo "[4/5] Iniciando Metastore..."
docker compose -f "$ROOT_DIR/metastore/docker-compose.yml" up -d

echo "[5/5] Iniciando Trino e Airflow..."
docker compose -f "$ROOT_DIR/trino/docker-compose.prod.yml" up -d
docker compose -f "$ROOT_DIR/airflow/docker-compose.yml" up -d

echo "Serviços iniciados. URLs:"
echo " - MinIO: http://localhost:9001"
echo " - Trino: http://localhost:8080"
echo " - Airflow: http://localhost:8083"


echo "[2/5] Criando rede Docker src_lakehouse (se não existir)..."
docker network inspect src_lakehouse >/dev/null 2>&1 || docker network create src_lakehouse

echo "[3/5] Iniciando Trino + Metastore + MinIO..."
cd "$ROOT_DIR/trino"
docker compose up -d

echo "[4/5] Iniciando Airflow..."
cd "$ROOT_DIR/airflow"
docker compose up -d

echo "[5/5] Verificando status dos serviços..."
for svc in trino metastore minio postgres redis airflow-apiserver; do
  if docker ps --filter "name=$svc" --format '{{.Names}}' | grep -q .; then
    echo "  - $svc: OK"
  else
    echo "  - $svc: NÃO ENCONTRADO"
  fi
done

echo "Concluído. Acesse:"
echo " - Trino: http://localhost:8080"
echo " - MinIO Console: http://localhost:9001"
echo " - Airflow: http://localhost:8083"
