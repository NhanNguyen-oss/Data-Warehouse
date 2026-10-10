"""Read-only PostgreSQL access for the London dashboard."""
from __future__ import annotations
import os
from pathlib import Path
import psycopg
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[2]

class DatabaseConfigurationError(ValueError):
    pass

def database_url(env_file: Path | None = None) -> str:
    """Environment overrides root .env; accept plain/quoted KEY=value lines."""
    value = os.environ.get("DW_DATABASE_URL")
    if value is None and os.environ.get("PGHOST"):
        return make_conninfo(
            host=os.environ["PGHOST"], port=os.environ.get("PGPORT", "5432"),
            dbname=os.environ.get("PGDATABASE", "road_safety_dw"),
            user=os.environ.get("PGUSER", "dw"), password=os.environ.get("PGPASSWORD", ""),
        )
    if value is None:
        path = env_file if env_file is not None else ROOT / ".env"
        if path.is_file():
            for line in path.read_text(encoding="utf-8-sig").splitlines():
                key, separator, candidate = line.partition("=")
                if separator and key.strip() == "DW_DATABASE_URL":
                    value = candidate.strip()
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                        value = value[1:-1]
    if not value or not value.strip():
        raise DatabaseConfigurationError("DW_DATABASE_URL is required")
    return value.strip()

# Aggregate each fact independently to avoid multiplying collision measures.
MONTHLY_SQL = """
WITH locations AS (
    SELECT location_key,
           CASE WHEN local_authority_highway = 'EHEATHROW'
                THEN 'E09000017' ELSE local_authority_highway END AS authority_code,
           CASE WHEN local_authority_highway = 'EHEATHROW'
                THEN 'Hillingdon' ELSE local_authority_highway_label END AS authority_name
    FROM dw.dim_location
), collisions AS (
    SELECT d.year, d.month_number, l.authority_code,
           MIN(l.authority_name) AS authority_name, COUNT(*) AS collisions
    FROM dw.fact_collision f
    JOIN dw.dim_date d USING (date_key)
    JOIN locations l USING (location_key)
    WHERE d.year BETWEEN 2021 AND 2025
      AND l.authority_code ~ '^E090000(0[1-9]|[12][0-9]|3[0-3])$'
    GROUP BY d.year, d.month_number, l.authority_code
), casualties AS (
    SELECT d.year, d.month_number, l.authority_code,
           SUM(f.casualty_count) AS casualties, SUM(f.fatal_count) AS fatalities,
           SUM(f.fatal_count + COALESCE(f.adjusted_serious, 0)) AS ksi_adjusted,
           COUNT(*) FILTER (WHERE f.adjusted_serious IS NULL AND f.fatal_count = 0)
               AS adjustment_missing
    FROM dw.fact_casualty f
    JOIN dw.dim_date d USING (date_key)
    JOIN locations l USING (location_key)
    WHERE d.year BETWEEN 2021 AND 2025
      AND l.authority_code ~ '^E090000(0[1-9]|[12][0-9]|3[0-3])$'
    GROUP BY d.year, d.month_number, l.authority_code
)
SELECT c.*, COALESCE(p.casualties, 0) AS casualties,
       COALESCE(p.fatalities, 0) AS fatalities,
       p.ksi_adjusted::double precision AS ksi_adjusted,
       COALESCE(p.adjustment_missing, 0) AS adjustment_missing
FROM collisions c
LEFT JOIN casualties p USING (year, month_number, authority_code)
ORDER BY year, month_number, authority_code
"""

def load_monthly_facts() -> list[dict]:
    with psycopg.connect(database_url(), connect_timeout=5, row_factory=dict_row) as conn:
        conn.read_only = True
        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout = '30s'")
            cur.execute(MONTHLY_SQL)
            return cur.fetchall()


if __name__ == "__main__":
    try:
        rows = load_monthly_facts()
    except DatabaseConfigurationError:
        print("Set DW_DATABASE_URL in the project .env or environment first.")
        raise SystemExit(1)
    except psycopg.Error:
        print("Cannot query the warehouse. Check host, port, database, credentials and dw schema.")
        raise SystemExit(1)
    print(f"Connected: {len(rows)} authority-month groups; "
          f"{len({row['authority_code'] for row in rows})} London authorities; "
          f"{sum(row['collisions'] for row in rows):,} collisions; "
          f"{sum(row['casualties'] for row in rows):,} casualties.")
