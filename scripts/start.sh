#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)

check_file() {
  if [[ ! -f "$1" ]]; then
    echo "ERRO: arquivo $1 não encontrado. Copie .env.example e ajuste as variáveis." >&2
    exit 1
  fi
}

check_file "$ROOT_DIR/.env"
check_file "$ROOT_DIR/airflow/.env"
check_file "$ROOT_DIR/trino/.env"

cp "$ROOT_DIR/.env" "$ROOT_DIR/minio/.env"
cp "$ROOT_DIR/.env" "$ROOT_DIR/metastore/.env"
cp "$ROOT_DIR/.env" "$ROOT_DIR/trino/.env"
cp "$ROOT_DIR/.env" "$ROOT_DIR/airflow/.env"

echo "[1/6] Criando rede Docker src_lakehouse (se não existir)..."
docker network inspect src_lakehouse >/dev/null 2>&1 || docker network create src_lakehouse

echo "[2/6] Iniciando MinIO..."
docker compose -f "$ROOT_DIR/minio/docker-compose.yml" up -d

echo "[3/6] Iniciando Metastore..."
docker compose -f "$ROOT_DIR/metastore/docker-compose.yml" up -d

echo "[4/6] Iniciando Trino..."
docker compose -f "$ROOT_DIR/trino/docker-compose.prod.yml" up -d

echo "[5/6] Iniciando Airflow..."
docker compose -f "$ROOT_DIR/airflow/docker-compose.yml" up -d

echo "[6/6] Verificando containers e saúde..."
services=(minio metastore-db metastore trino postgres redis airflow-apiserver)
for svc in "${services[@]}"; do
  if docker ps --filter "name=$svc" --format '{{.Names}}' | grep -q .; then
    echo "  - $svc: RUNNING"
  else
    echo "  - $svc: NOT RUNNING"
  fi
done

echo "Concluído. Acesse:"
echo " - MinIO: http://localhost:9001"
echo " - Trino: http://localhost:8080"
echo " - Airflow: http://localhost:8083"

