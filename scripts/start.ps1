param()

$RootScript = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Resolve-Path "$RootScript\.."

Write-Host "[1/5] Verificando arquivos de configuração..."
foreach ($file in @("$Root\.env", "$Root\airflow\.env", "$Root\trino\.env")) {
  if (-Not (Test-Path $file)) {
    Write-Error "ERRO: arquivo $file não encontrado. Copie .env.example e ajuste as variáveis."; exit 1
  }
}

Copy-Item "$Root\.env" "$Root\trino\.env" -Force
Copy-Item "$Root\.env" "$Root\metastore\.env" -Force
Copy-Item "$Root\.env" "$Root\minio\.env" -Force
Copy-Item "$Root\.env" "$Root\airflow\.env" -Force

Write-Host "[2/5] Criando rede Docker src_lakehouse (se não existir)..."
if (-Not (docker network ls --format '{{.Name}}' | Select-String -Pattern '^src_lakehouse$')) { docker network create src_lakehouse }

Write-Host "[3/5] Iniciando MinIO..."
Set-Location "$Root\minio"
docker compose up -d

Write-Host "[4/5] Iniciando Metastore..."
Set-Location "$Root\metastore"
docker compose up -d

Write-Host "[5/5] Iniciando Trino e Airflow..."
Set-Location "$Root\trino"
docker compose -f docker-compose.prod.yml up -d

Set-Location "$Root\airflow"
docker compose up -d

Write-Host "Serviços iniciados. URLs:"
Write-Host " - MinIO: http://localhost:9001"
Write-Host " - Trino: http://localhost:8080"
Write-Host " - Airflow: http://localhost:8083"


Write-Host "[2/5] Criando rede Docker src_lakehouse (se não existir)..."
if (-Not (docker network ls --format '{{.Name}}' | Select-String -Pattern '^src_lakehouse$')) { docker network create src_lakehouse }

Write-Host "[3/5] Iniciando Trino + Metastore + MinIO..."
Set-Location "$Root\trino"
docker compose up -d

Write-Host "[4/5] Iniciando Airflow..."
Set-Location "$Root\airflow"
docker compose up -d

Write-Host "[5/5] Verificando status dos serviços..."
$services = "trino", "metastore", "minio", "postgres", "redis", "airflow-apiserver"
foreach ($svc in $services) {
  $running = docker ps --filter "name=$svc" --format '{{.Names}}' | Select-String -Pattern '.'
  if ($running) { Write-Host "  - $svc: OK" } else { Write-Host "  - $svc: NÃO ENCONTRADO" }
}

Write-Host "Concluído. Acesse:"
Write-Host " - Trino: http://localhost:8080"
Write-Host " - MinIO Console: http://localhost:9001"
Write-Host " - Airflow: http://localhost:8083"
