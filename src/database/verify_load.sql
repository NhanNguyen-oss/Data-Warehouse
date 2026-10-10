-- Read-only checks for the full STATS19 2021-2025 baseline load.
-- Expected counts describe the committed source manifest, not a London-only load.
\set ON_ERROR_STOP on

SELECT 'fact_collision' AS table_name, COUNT(*) AS actual_rows,
       513801 AS expected_rows, COUNT(*) = 513801 AS passed
FROM dw.fact_collision
UNION ALL
SELECT 'fact_vehicle', COUNT(*), 937265, COUNT(*) = 937265
FROM dw.fact_vehicle
UNION ALL
SELECT 'fact_casualty', COUNT(*), 652821, COUNT(*) = 652821
FROM dw.fact_casualty;

SELECT SUM(number_of_vehicles) AS declared_vehicles,
       (SELECT COUNT(*) FROM dw.fact_vehicle) AS loaded_vehicles,
       SUM(number_of_vehicles) = (SELECT COUNT(*) FROM dw.fact_vehicle)
           AS vehicles_match,
       SUM(number_of_casualties) AS declared_casualties,
       (SELECT COUNT(*) FROM dw.fact_casualty) AS loaded_casualties,
       SUM(number_of_casualties) = (SELECT COUNT(*) FROM dw.fact_casualty)
           AS casualties_match
FROM dw.fact_collision;

SELECT d.year, COUNT(*) AS collisions
FROM dw.fact_collision f
JOIN dw.dim_date d ON d.date_key = f.date_key
GROUP BY d.year
ORDER BY d.year;

-- The old view's ksi_adjusted is collision-level, not casualty-level KSI persons.
-- Check only its collision/casualty totals here; S4 will define the London mart.
SELECT SUM(collisions) = (SELECT COUNT(*) FROM dw.fact_collision)
           AS view_collisions_match,
       SUM(casualties) = (SELECT COUNT(*) FROM dw.fact_casualty)
           AS view_casualties_match
FROM dw.v_local_authority_year;
