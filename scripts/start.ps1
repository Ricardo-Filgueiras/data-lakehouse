param()

$RootScript = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Resolve-Path "$RootScript\.."

$requiredFiles = @("$Root\.env", "$Root\airflow\.env", "$Root\trino\.env")
foreach ($file in $requiredFiles) {
  if (-Not (Test-Path $file)) {
    Write-Error "ERRO: arquivo $file não encontrado. Copie .env.example e ajuste as variáveis."; exit 1
  }
}

Copy-Item "$Root\.env" "$Root\minio\.env" -Force
Copy-Item "$Root\.env" "$Root\metastore\.env" -Force
Copy-Item "$Root\.env" "$Root\trino\.env" -Force
Copy-Item "$Root\.env" "$Root\airflow\.env" -Force

Write-Host "[1/6] Criando rede Docker src_lakehouse (se não existir)..."
if (-Not (docker network ls --format '{{.Name}}' | Select-String -Pattern '^src_lakehouse$')) { docker network create src_lakehouse }

Write-Host "[2/6] Iniciando MinIO..."
Set-Location "$Root\minio"
docker compose up -d

Write-Host "[3/6] Iniciando Metastore..."
Set-Location "$Root\metastore"
docker compose up -d

Write-Host "[4/6] Iniciando Trino..."
Set-Location "$Root\trino"
docker compose -f docker-compose.prod.yml up -d

Write-Host "[5/6] Iniciando Airflow..."
Set-Location "$Root\airflow"
docker compose up -d

Write-Host "[6/6] Verificando containers..."
$services = @("minio", "createbucket", "metastore-db", "create-metastore-schema", "metastore", "trino", "postgres", "redis", "airflow-apiserver")
foreach ($svc in $services) {
  $running = docker ps --filter "name=$svc" --format '{{.Names}}'
  if ($running) { Write-Host "  - $svc: RUNNING" } else { Write-Host "  - $svc: NOT RUNNING" }
}

Write-Host "Concluído. URLs:"
Write-Host " - MinIO: http://localhost:9001"
Write-Host " - Trino: http://localhost:8080"
Write-Host " - Airflow: http://localhost:8083"

