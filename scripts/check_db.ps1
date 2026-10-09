# Stage S0 container health check. Run from the repository root after starting Docker Desktop:
#   powershell -ExecutionPolicy Bypass -File scripts\check_db.ps1
# psql is not needed on the host; it runs inside the db container.

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    "Created .env from .env.example. Change POSTGRES_PASSWORD (and DW_DATABASE_URL) before real use."
}

docker info --format "{{.ServerVersion}}" *> $null
if ($LASTEXITCODE -ne 0) { throw "Docker engine is not running. Start Docker Desktop and rerun." }

docker compose up -d db
if ($LASTEXITCODE -ne 0) { throw "docker compose up failed." }

$status = ""
for ($i = 0; $i -lt 60; $i++) {
    $status = (docker inspect --format "{{.State.Health.Status}}" (docker compose ps -q db)).Trim()
    if ($status -eq "healthy") { break }
    Start-Sleep -Seconds 2
}
"{0,-16} {1}" -f "db health", $status
if ($status -ne "healthy") {
    docker compose logs --tail 50 db
    throw "db container did not become healthy."
}

docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "select version()"'
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "select postgis_full_version()"'
$tables = docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "select count(*) from information_schema.tables where table_schema = ''dw''"'
"{0,-16} {1}" -f "dw tables", $tables.Trim()
