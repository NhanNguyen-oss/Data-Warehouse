-- =============================================================================
-- CO4031 | Kho dữ liệu và Hệ hỗ trợ Quyết định (HK261)
-- File: src/database/schema.sql
-- Đề tài: kho dữ liệu tai nạn giao thông đường bộ Anh (STATS19, DfT), 2021–2025.
--
-- Mô hình: FACT CONSTELLATION (galaxy) — ba bảng fact theo ba mức chi tiết,
-- mỗi fact là một star schema, dùng chung các conformed dimension.
--
--   fact_collision  grain: một vụ va chạm                (collision_index)
--   fact_vehicle    grain: một xe trong một vụ           (collision_index, vehicle_reference)
--   fact_casualty   grain: một nạn nhân                  (collision_index, vehicle_reference, casualty_reference)
--
--   Conformed dimension: dim_date, dim_time, dim_location, dim_road,
--                        dim_conditions, dim_severity
--   Dimension riêng:     dim_vehicle, dim_driver, dim_vehicle_action (fact_vehicle)
--                        dim_casualty, dim_vehicle (fact_casualty)
--
-- Không nối fact với fact. Muốn phân tích chéo (ví dụ nạn nhân theo điều kiện
-- đường) thì đi qua dimension dùng chung; collision_index giữ lại làm
-- degenerate dimension để truy vết về nguồn.
--
-- Khóa surrogate do ETL (src/etl/pipeline.py) sinh và ghi sẵn trong CSV,
-- nên các cột khóa không dùng SERIAL/IDENTITY.
--
-- Quy ước mã hóa:
--   <cột>        mã gốc của STATS19 (-1 = thiếu dữ liệu)
--   <cột>_label  nhãn tra từ bảng mã chính thức của DfT (data guide 2025)
--   Cột mã dạng chuỗi (quận huyện, LSOA) thiếu dữ liệu ghi 'UNKNOWN'.
--
-- Cú pháp: PostgreSQL 13+.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS dw;

-- -----------------------------------------------------------------------------
-- Conformed dimension: thời gian
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_date (
    date_key      INTEGER     PRIMARY KEY,         -- YYYYMMDD
    full_date     DATE        NOT NULL UNIQUE,
    day_of_month  SMALLINT    NOT NULL,
    day_of_week   SMALLINT    NOT NULL,            -- ISO: 1 = Monday ... 7 = Sunday
    day_name      VARCHAR(10) NOT NULL,
    is_weekend    SMALLINT    NOT NULL,            -- 1 = Saturday/Sunday
    week_of_year  SMALLINT    NOT NULL,            -- ISO week
    month_number  SMALLINT    NOT NULL,
    month_name    VARCHAR(10) NOT NULL,
    quarter       SMALLINT    NOT NULL,
    year          SMALLINT    NOT NULL
);

CREATE TABLE IF NOT EXISTS dw.dim_time (
    time_key      SMALLINT    PRIMARY KEY,         -- HHMM, -1 = không rõ
    hour          SMALLINT,
    minute        SMALLINT,
    time_band     VARCHAR(30) NOT NULL,            -- Night / Morning peak / Daytime / Evening peak / Evening
    is_peak_hour  SMALLINT    NOT NULL             -- 1 = khung 06-09 hoặc 16-19
);

-- -----------------------------------------------------------------------------
-- Conformed dimension: mức độ nghiêm trọng (dùng cho cả vụ va chạm và nạn nhân)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_severity (
    severity_key    SMALLINT PRIMARY KEY,          -- 1 Fatal, 2 Serious, 3 Slight
    severity_label  TEXT     NOT NULL
);

-- -----------------------------------------------------------------------------
-- Conformed dimension: địa điểm
-- Phân cấp: LSOA -> local authority (ONS district) ; police force song song.
-- Muốn snowflake: tách (local_authority_ons_district, *_label) và police_force
-- ra dim_local_authority / dim_police_force rồi giữ FK ở đây.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_location (
    location_key                        INTEGER     PRIMARY KEY,
    police_force                        SMALLINT    NOT NULL,
    police_force_label                  TEXT        NOT NULL,
    local_authority_ons_district        VARCHAR(12) NOT NULL,
    local_authority_ons_district_label  TEXT        NOT NULL,
    local_authority_highway             VARCHAR(12) NOT NULL,
    local_authority_highway_label       TEXT        NOT NULL,
    lsoa_code                           VARCHAR(12) NOT NULL,
    urban_or_rural_area                 SMALLINT    NOT NULL,
    urban_or_rural_area_label           TEXT        NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dim_location_la
    ON dw.dim_location (local_authority_ons_district);

-- -----------------------------------------------------------------------------
-- Conformed dimension: đặc điểm đường tại nơi xảy ra va chạm
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_road (
    road_key                   INTEGER  PRIMARY KEY,
    first_road_class           SMALLINT NOT NULL,
    first_road_class_label     TEXT     NOT NULL,
    road_type                  SMALLINT NOT NULL,
    road_type_label            TEXT     NOT NULL,
    junction_detail            SMALLINT NOT NULL,
    junction_detail_label      TEXT     NOT NULL,
    junction_control           SMALLINT NOT NULL,
    junction_control_label     TEXT     NOT NULL,
    second_road_class          SMALLINT NOT NULL,
    second_road_class_label    TEXT     NOT NULL,
    pedestrian_crossing        SMALLINT NOT NULL,
    pedestrian_crossing_label  TEXT     NOT NULL,
    trunk_road_flag            SMALLINT NOT NULL,
    trunk_road_flag_label      TEXT     NOT NULL,
    speed_limit                SMALLINT NOT NULL      -- mph, -1 = thiếu dữ liệu
);

-- -----------------------------------------------------------------------------
-- Conformed dimension (junk): điều kiện môi trường lúc va chạm
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_conditions (
    conditions_key                    INTEGER  PRIMARY KEY,
    light_conditions                  SMALLINT NOT NULL,
    light_conditions_label            TEXT     NOT NULL,
    weather_conditions                SMALLINT NOT NULL,
    weather_conditions_label          TEXT     NOT NULL,
    road_surface_conditions           SMALLINT NOT NULL,
    road_surface_conditions_label     TEXT     NOT NULL,
    special_conditions_at_site        SMALLINT NOT NULL,
    special_conditions_at_site_label  TEXT     NOT NULL,
    carriageway_hazards               SMALLINT NOT NULL,
    carriageway_hazards_label         TEXT     NOT NULL
);

-- -----------------------------------------------------------------------------
-- Dimension cho fact_vehicle và fact_casualty: hồ sơ phương tiện
-- generic_make_model không đưa vào (quá nhiều giá trị, ~24% thiếu).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_vehicle (
    vehicle_key                    INTEGER     PRIMARY KEY,
    vehicle_type                   SMALLINT    NOT NULL,
    vehicle_type_label             TEXT        NOT NULL,
    propulsion_code                SMALLINT    NOT NULL,
    propulsion_code_label          TEXT        NOT NULL,
    towing_and_articulation        SMALLINT    NOT NULL,
    towing_and_articulation_label  TEXT        NOT NULL,
    vehicle_left_hand_drive        SMALLINT    NOT NULL,
    vehicle_left_hand_drive_label  TEXT        NOT NULL,
    escooter_flag                  SMALLINT    NOT NULL,
    escooter_flag_label            TEXT        NOT NULL,
    engine_capacity_band           VARCHAR(20) NOT NULL,
    vehicle_age_band               VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS dw.dim_driver (
    driver_key                       INTEGER  PRIMARY KEY,
    sex_of_driver                    SMALLINT NOT NULL,
    sex_of_driver_label              TEXT     NOT NULL,
    age_band_of_driver               SMALLINT NOT NULL,
    age_band_of_driver_label         TEXT     NOT NULL,
    driver_imd_decile                SMALLINT NOT NULL,
    driver_imd_decile_label          TEXT     NOT NULL,
    journey_purpose_of_driver        SMALLINT NOT NULL,
    journey_purpose_of_driver_label  TEXT     NOT NULL
);

-- Junk dimension: hành vi và diễn biến của xe trong vụ va chạm
CREATE TABLE IF NOT EXISTS dw.dim_vehicle_action (
    action_key                         INTEGER  PRIMARY KEY,
    vehicle_manoeuvre                  SMALLINT NOT NULL,
    vehicle_manoeuvre_label            TEXT     NOT NULL,
    junction_location                  SMALLINT NOT NULL,
    junction_location_label            TEXT     NOT NULL,
    skidding_and_overturning           SMALLINT NOT NULL,
    skidding_and_overturning_label     TEXT     NOT NULL,
    hit_object_in_carriageway          SMALLINT NOT NULL,
    hit_object_in_carriageway_label    TEXT     NOT NULL,
    vehicle_leaving_carriageway        SMALLINT NOT NULL,
    vehicle_leaving_carriageway_label  TEXT     NOT NULL,
    hit_object_off_carriageway         SMALLINT NOT NULL,
    hit_object_off_carriageway_label   TEXT     NOT NULL,
    first_point_of_impact              SMALLINT NOT NULL,
    first_point_of_impact_label        TEXT     NOT NULL
);

-- -----------------------------------------------------------------------------
-- Dimension cho fact_casualty: hồ sơ nạn nhân
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_casualty (
    casualty_profile_key          INTEGER  PRIMARY KEY,
    casualty_class                SMALLINT NOT NULL,
    casualty_class_label          TEXT     NOT NULL,
    sex_of_casualty               SMALLINT NOT NULL,
    sex_of_casualty_label         TEXT     NOT NULL,
    age_band_of_casualty          SMALLINT NOT NULL,
    age_band_of_casualty_label    TEXT     NOT NULL,
    casualty_type                 SMALLINT NOT NULL,
    casualty_type_label           TEXT     NOT NULL,
    casualty_imd_decile           SMALLINT NOT NULL,
    casualty_imd_decile_label     TEXT     NOT NULL,
    pedestrian_location           SMALLINT NOT NULL,
    pedestrian_location_label     TEXT     NOT NULL,
    pedestrian_movement           SMALLINT NOT NULL,
    pedestrian_movement_label     TEXT     NOT NULL,
    car_passenger                 SMALLINT NOT NULL,
    car_passenger_label           TEXT     NOT NULL,
    bus_or_coach_passenger        SMALLINT NOT NULL,
    bus_or_coach_passenger_label  TEXT     NOT NULL,
    escooter_flag                 SMALLINT NOT NULL,
    escooter_flag_label           TEXT     NOT NULL
);

-- -----------------------------------------------------------------------------
-- Fact 1: vụ va chạm (transaction fact)
-- Measure:
--   additive      number_of_vehicles, number_of_casualties,
--                 fatal_count / serious_count / slight_count (cờ 0/1, SUM = số vụ)
--   additive      adjusted_serious, adjusted_slight: xác suất đã hiệu chỉnh của DfT
--                 do một số lực lượng cảnh sát chuyển sang ghi nhận theo thương tích.
--                 SUM = số vụ nặng/nhẹ đã hiệu chỉnh; vụ Fatal có cả hai = 0.
--                 So sánh giữa các năm/địa bàn nên dùng số đã hiệu chỉnh:
--                 KSI hiệu chỉnh = SUM(fatal_count) + SUM(adjusted_serious).
--   cờ            injury_based_reporting, police_attended
--   không cộng    longitude, latitude (dùng để vẽ bản đồ)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.fact_collision (
    collision_key           BIGINT       PRIMARY KEY,
    collision_index         VARCHAR(20)  NOT NULL UNIQUE,
    date_key                INTEGER      NOT NULL REFERENCES dw.dim_date (date_key),
    time_key                SMALLINT     NOT NULL REFERENCES dw.dim_time (time_key),
    location_key            INTEGER      NOT NULL REFERENCES dw.dim_location (location_key),
    road_key                INTEGER      NOT NULL REFERENCES dw.dim_road (road_key),
    conditions_key          INTEGER      NOT NULL REFERENCES dw.dim_conditions (conditions_key),
    severity_key            SMALLINT     NOT NULL REFERENCES dw.dim_severity (severity_key),
    number_of_vehicles      SMALLINT     NOT NULL,
    number_of_casualties    SMALLINT     NOT NULL,
    fatal_count             SMALLINT     NOT NULL,
    serious_count           SMALLINT     NOT NULL,
    slight_count            SMALLINT     NOT NULL,
    adjusted_serious        NUMERIC(9, 6),
    adjusted_slight         NUMERIC(9, 6),
    injury_based_reporting  SMALLINT     NOT NULL,
    police_attended         SMALLINT     NOT NULL,
    longitude               NUMERIC(9, 6),
    latitude                NUMERIC(9, 6)
);

CREATE INDEX IF NOT EXISTS idx_fact_collision_date     ON dw.fact_collision (date_key);
CREATE INDEX IF NOT EXISTS idx_fact_collision_location ON dw.fact_collision (location_key);
CREATE INDEX IF NOT EXISTS idx_fact_collision_severity ON dw.fact_collision (severity_key);

-- -----------------------------------------------------------------------------
-- Fact 2: xe trong vụ va chạm
-- Dimension của vụ (ngày, giờ, địa điểm, đường, điều kiện, mức độ vụ) được
-- ETL sao chép xuống để truy vấn không phải đi qua fact_collision.
-- age_of_driver, engine_capacity_cc, age_of_vehicle: NULL khi nguồn ghi -1;
-- chỉ dùng AVG/MIN/MAX, không SUM.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.fact_vehicle (
    vehicle_fact_key        BIGINT       PRIMARY KEY,
    collision_index         VARCHAR(20)  NOT NULL,
    vehicle_reference       SMALLINT     NOT NULL,
    date_key                INTEGER      NOT NULL REFERENCES dw.dim_date (date_key),
    time_key                SMALLINT     NOT NULL REFERENCES dw.dim_time (time_key),
    location_key            INTEGER      NOT NULL REFERENCES dw.dim_location (location_key),
    road_key                INTEGER      NOT NULL REFERENCES dw.dim_road (road_key),
    conditions_key          INTEGER      NOT NULL REFERENCES dw.dim_conditions (conditions_key),
    collision_severity_key  SMALLINT     NOT NULL REFERENCES dw.dim_severity (severity_key),
    vehicle_key             INTEGER      NOT NULL REFERENCES dw.dim_vehicle (vehicle_key),
    driver_key              INTEGER      NOT NULL REFERENCES dw.dim_driver (driver_key),
    action_key              INTEGER      NOT NULL REFERENCES dw.dim_vehicle_action (action_key),
    vehicle_count           SMALLINT     NOT NULL,
    age_of_driver           SMALLINT,
    engine_capacity_cc      INTEGER,
    age_of_vehicle          SMALLINT,
    UNIQUE (collision_index, vehicle_reference)
);

CREATE INDEX IF NOT EXISTS idx_fact_vehicle_date    ON dw.fact_vehicle (date_key);
CREATE INDEX IF NOT EXISTS idx_fact_vehicle_vehicle ON dw.fact_vehicle (vehicle_key);

-- -----------------------------------------------------------------------------
-- Fact 3: nạn nhân
-- severity_key là mức độ của chính nạn nhân (casualty_severity).
-- vehicle_key: hồ sơ xe mà nạn nhân đi trên đó, hoặc xe đâm vào người đi bộ.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.fact_casualty (
    casualty_fact_key     BIGINT       PRIMARY KEY,
    collision_index       VARCHAR(20)  NOT NULL,
    vehicle_reference     SMALLINT     NOT NULL,
    casualty_reference    SMALLINT     NOT NULL,
    date_key              INTEGER      NOT NULL REFERENCES dw.dim_date (date_key),
    time_key              SMALLINT     NOT NULL REFERENCES dw.dim_time (time_key),
    location_key          INTEGER      NOT NULL REFERENCES dw.dim_location (location_key),
    road_key              INTEGER      NOT NULL REFERENCES dw.dim_road (road_key),
    conditions_key        INTEGER      NOT NULL REFERENCES dw.dim_conditions (conditions_key),
    severity_key          SMALLINT     NOT NULL REFERENCES dw.dim_severity (severity_key),
    casualty_profile_key  INTEGER      NOT NULL REFERENCES dw.dim_casualty (casualty_profile_key),
    vehicle_key           INTEGER      REFERENCES dw.dim_vehicle (vehicle_key),
    casualty_count        SMALLINT     NOT NULL,
    fatal_count           SMALLINT     NOT NULL,
    serious_count         SMALLINT     NOT NULL,
    slight_count          SMALLINT     NOT NULL,
    adjusted_serious      NUMERIC(9, 6),
    adjusted_slight       NUMERIC(9, 6),
    age_of_casualty       SMALLINT,
    UNIQUE (collision_index, vehicle_reference, casualty_reference)
);

CREATE INDEX IF NOT EXISTS idx_fact_casualty_date     ON dw.fact_casualty (date_key);
CREATE INDEX IF NOT EXISTS idx_fact_casualty_location ON dw.fact_casualty (location_key);
CREATE INDEX IF NOT EXISTS idx_fact_casualty_profile  ON dw.fact_casualty (casualty_profile_key);

-- -----------------------------------------------------------------------------
-- View tổng hợp cho dashboard và DSS: an toàn giao thông theo quận huyện, năm
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW dw.v_local_authority_year AS
SELECT
    l.local_authority_ons_district                             AS la_code,
    l.local_authority_ons_district_label                       AS la_name,
    d.year,
    COUNT(*)                                                   AS collisions,
    SUM(f.number_of_casualties)                                AS casualties,
    SUM(f.fatal_count)                                         AS fatal_collisions,
    SUM(f.serious_count)                                       AS serious_collisions,
    ROUND(SUM(f.fatal_count) + SUM(f.adjusted_serious), 2)     AS ksi_adjusted,
    ROUND((SUM(f.fatal_count) + SUM(f.adjusted_serious))
          / NULLIF(COUNT(*), 0), 4)                            AS ksi_share
FROM dw.fact_collision f
JOIN dw.dim_location l ON l.location_key = f.location_key
JOIN dw.dim_date d     ON d.date_key = f.date_key
GROUP BY l.local_authority_ons_district, l.local_authority_ons_district_label, d.year;

-- -----------------------------------------------------------------------------
-- Truy vấn OLAP mẫu (chạy sau khi ETL đã nạp dữ liệu)
-- -----------------------------------------------------------------------------

-- Roll-up: nạn nhân theo năm và mức độ
-- SELECT d.year, s.severity_label, SUM(f.casualty_count) AS casualties
-- FROM dw.fact_casualty f
-- JOIN dw.dim_date d     ON d.date_key = f.date_key
-- JOIN dw.dim_severity s ON s.severity_key = f.severity_key
-- GROUP BY d.year, s.severity_label
-- ORDER BY d.year, s.severity_label;

-- Drill-down: từ năm xuống tháng (năm 2025)
-- SELECT d.month_number, d.month_name, COUNT(*) AS collisions,
--        SUM(f.fatal_count) + SUM(f.adjusted_serious) AS ksi_adjusted
-- FROM dw.fact_collision f
-- JOIN dw.dim_date d ON d.date_key = f.date_key
-- WHERE d.year = 2025
-- GROUP BY d.month_number, d.month_name
-- ORDER BY d.month_number;

-- Slice: chỉ các vụ trong bóng tối, theo loại đường
-- SELECT r.road_type_label, COUNT(*) AS collisions, SUM(f.fatal_count) AS fatal
-- FROM dw.fact_collision f
-- JOIN dw.dim_conditions c ON c.conditions_key = f.conditions_key
-- JOIN dw.dim_road r       ON r.road_key = f.road_key
-- WHERE c.light_conditions_label LIKE 'Darkness%'
-- GROUP BY r.road_type_label
-- ORDER BY collisions DESC;

-- Dice: đô thị, giới hạn 30 mph, mặt đường ướt — theo năm và khung giờ
-- SELECT d.year, t.time_band, COUNT(*) AS collisions
-- FROM dw.fact_collision f
-- JOIN dw.dim_date d       ON d.date_key = f.date_key
-- JOIN dw.dim_time t       ON t.time_key = f.time_key
-- JOIN dw.dim_location l   ON l.location_key = f.location_key
-- JOIN dw.dim_road r       ON r.road_key = f.road_key
-- JOIN dw.dim_conditions c ON c.conditions_key = f.conditions_key
-- WHERE l.urban_or_rural_area = 1
--   AND r.speed_limit = 30
--   AND c.road_surface_conditions = 2
-- GROUP BY d.year, t.time_band
-- ORDER BY d.year, t.time_band;

-- Phân tích chéo fact_casualty x dim_vehicle: người đi bộ bị loại xe nào gây thương vong
-- SELECT v.vehicle_type_label, SUM(f.casualty_count) AS pedestrians,
--        SUM(f.fatal_count) AS pedestrian_deaths
-- FROM dw.fact_casualty f
-- JOIN dw.dim_casualty p ON p.casualty_profile_key = f.casualty_profile_key
-- JOIN dw.dim_vehicle v  ON v.vehicle_key = f.vehicle_key
-- WHERE p.casualty_class = 3
-- GROUP BY v.vehicle_type_label
-- ORDER BY pedestrians DESC;

-- Đầu vào DSS: 10 quận huyện có KSI hiệu chỉnh cao nhất năm 2025
-- SELECT la_name, collisions, ksi_adjusted, ksi_share
-- FROM dw.v_local_authority_year
-- WHERE year = 2025
-- ORDER BY ksi_adjusted DESC
-- LIMIT 10;
