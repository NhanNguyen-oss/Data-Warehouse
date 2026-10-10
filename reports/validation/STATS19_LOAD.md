# STATS19 baseline load verification

Date: 2026-10-10 (Asia/Bangkok).

## Scope

The existing STATS19 loader generated the full Great Britain 2021–2025 baseline. The confirmed analytical MVP is London, 2021–2025 (D13); London filtering and traffic integration belong to S4/S5.

## Results

| Table | Expected | Database | Result |
| --- | ---: | ---: | --- |
| dw.fact_collision | 513801 | 513801 | Pass |
| dw.fact_vehicle | 937265 | 937265 | Pass |
| dw.fact_casualty | 652821 | 652821 | Pass |

- Vehicles declared by collisions: 937265; loaded vehicle rows: 937265.
- Casualties declared by collisions: 652821; loaded casualty rows: 652821.
- Existing authority-year view totals match collision and casualty totals.
- Collision years: 2021 = 101087; 2022 = 106004; 2023 = 104258; 2024 = 100927; 2025 = 101525.
- All 16 existing unit tests passed under Python 3.13.1.

## Execution and limitations

ETL CSV generation completed with no discarded rows; `data/processed/etl_report.csv` records reconciliation. Local `.venv` uses Python 3.13.1 and psycopg 3.3.6.

The host connection using `DW_DATABASE_URL` failed password authentication. Retrying with container environment credentials on the host port also failed. The reason has not been established; do not assume the host port reaches the intended instance or reset database credentials without investigation.

The generated CSVs were loaded through `docker compose exec -T db` and the container's local PostgreSQL socket with psql, in one BEGIN/TRUNCATE/COPY/COMMIT transaction. Two preliminary streaming attempts failed on Windows CSV line endings and rolled back. Normalizing CRLF to LF for streaming succeeded. No secrets are included in this report.

Read-only checks are in `src/database/verify_load.sql`. Run from PowerShell:

```powershell
Get-Content -Raw src/database/verify_load.sql | docker compose exec -T db sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB -v ON_ERROR_STOP=1'
```

This verifies row counts and totals; it does not establish that the old view's collision-level `ksi_adjusted` is casualty-level KSI persons. S4 must define the London mart and each measure explicitly. The host `pipeline.py --load` path remains unverified until authentication is resolved.

## Follow-up: dashboard connection (2026-10-10)

The user confirmed their working connection was local psql inside Docker. Password authentication to hostname `db` initially failed. The database role password was synchronized to the running container's configured `POSTGRES_PASSWORD`, without modifying warehouse data. A subsequent internal-network query succeeded and returned 513801 collisions.

The Windows host connection was then verified with the running container credentials. The git-ignored .env URL was synchronized to those settings. The dashboard query returned 33 authorities and 1980 monthly groups; its live Streamlit AppTest displayed 111454 collisions, 128035 casualties, 486 fatalities and adjusted casualty-level KSI 18981.9. Collision and casualty totals independently reconcile with raw STATS19. All 23 tests pass. The existing localhost:8501 server responds HTTP 200.

The user confirmed DBeaver connectivity using user dw and database road_safety_dw. A trial Docker-dashboard build was stopped; its Compose/Dockerfile changes were removed. PostgreSQL remains in Docker and the dashboard runs on Windows. The host ETL --load command has not been rerun after the authentication repair.
