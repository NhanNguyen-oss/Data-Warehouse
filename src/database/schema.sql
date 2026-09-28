-- =============================================================================
-- CO4031 | Kho dữ liệu và Hệ hỗ trợ Quyết định (HK261)
-- File: src/database/schema.sql
-- Mục đích: khung thiết kế kho dữ liệu đa chiều.
--
-- Mô hình mặc định: STAR SCHEMA (Kimball).
--   - Bảng fact nằm ở trung tâm, chứa measure và khóa ngoại tới dimension.
--   - Mỗi dimension là một bảng phẳng, phục vụ lọc / nhóm / drill-down.
--
-- Khi nào chuyển sang SNOWFLAKE:
--   - Một thuộc tính phân cấp (ví dụ category -> subcategory) được chuẩn hóa
--     thành bảng dimension riêng để tránh lặp và quản lý thay đổi độc lập.
--   - Khung snowflake mẫu nằm ở cuối file (dim_category).
--
-- Cú pháp: PostgreSQL.
--   SQL Server: BIGSERIAL -> BIGINT IDENTITY(1,1), BOOLEAN -> BIT.
--   MySQL:      BIGSERIAL -> BIGINT AUTO_INCREMENT, BOOLEAN -> TINYINT(1).
--
-- Việc nhóm phải làm trước khi viết DDL:
--   1. Chốt grain của fact (một dòng biểu diễn sự kiện nào?).
--   2. Liệt kê measure: additive / semi-additive / non-additive.
--   3. Liệt kê dimension và thuộc tính dùng để slice, dice, drill-down.
--   4. Quyết định SCD (thường Type 2 cho thuộc tính hay đổi theo thời gian).
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS dw;

-- -----------------------------------------------------------------------------
-- 1. Conformed dimension: Thời gian
-- Dùng chung cho mọi fact. date_key dạng YYYYMMDD để join dễ đọc khi debug.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_date (
    date_key      INTEGER      PRIMARY KEY,
    full_date     DATE         NOT NULL UNIQUE,
    day_of_month  SMALLINT     NOT NULL,
    day_of_week   SMALLINT     NOT NULL,          -- 1 = Monday ... 7 = Sunday
    day_name      VARCHAR(10)  NOT NULL,
    week_of_year  SMALLINT     NOT NULL,
    month_number  SMALLINT     NOT NULL,
    month_name    VARCHAR(12)  NOT NULL,
    quarter       SMALLINT     NOT NULL,
    year          SMALLINT     NOT NULL,
    is_weekend    BOOLEAN      NOT NULL
);

-- -----------------------------------------------------------------------------
-- 2. Dimension nghiệp vụ (ĐỔI TÊN VÀ CỘT theo đề tài)
-- Ví dụ: dim_product, dim_customer, dim_store, dim_student, dim_route...
-- SCD Type 2: mỗi lần thuộc tính thay đổi thì đóng phiên bản cũ, mở phiên bản mới.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_entity (
    entity_key      BIGSERIAL    PRIMARY KEY,     -- surrogate key, chỉ dùng trong DW
    entity_id       VARCHAR(64)  NOT NULL,        -- business key từ hệ thống nguồn
    entity_name     VARCHAR(255) NOT NULL,
    category_code   VARCHAR(64),                  -- FK logic sang dim_category nếu snowflake
    category_name   VARCHAR(100),                 -- denormalize để giữ star schema
    segment         VARCHAR(100),
    -- TODO: thêm thuộc tính phân tích và phân cấp (hierarchy) của đề tài
    effective_from  DATE         NOT NULL,
    effective_to    DATE,                         -- NULL = phiên bản hiện hành
    is_current      BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_dim_entity_business
    ON dw.dim_entity (entity_id, is_current);

-- -----------------------------------------------------------------------------
-- 3. Fact (ĐỔI TÊN, GRAIN VÀ MEASURE theo đề tài)
-- Grain gợi ý: một dòng = một sự kiện nghiệp vụ ở mức chi tiết đã chốt.
--   Transaction fact:        một giao dịch / một lần phát sinh.
--   Periodic snapshot fact:  trạng thái định kỳ (tồn kho cuối ngày, dư nợ cuối tháng).
--   Accumulating snapshot:   một quy trình có nhiều mốc ngày (đơn hàng -> giao -> thu tiền).
--
-- Measure:
--   additive        cộng được theo mọi dimension (amount, quantity)
--   semi-additive   không cộng theo thời gian (balance, on_hand)
--   non-additive    tỷ lệ, đơn giá — lưu thành phần tử/mẫu số, tính ở tầng truy vấn
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.fact_event (
    event_key      BIGSERIAL      PRIMARY KEY,
    date_key       INTEGER        NOT NULL REFERENCES dw.dim_date (date_key),
    entity_key     BIGINT         NOT NULL REFERENCES dw.dim_entity (entity_key),
    -- TODO: thêm FK tới các dimension khác của đề tài
    quantity       NUMERIC(18, 4),
    amount         NUMERIC(18, 2),
    source_txn_id  VARCHAR(64)                          -- degenerate dimension
);

CREATE INDEX IF NOT EXISTS idx_fact_event_date
    ON dw.fact_event (date_key);

CREATE INDEX IF NOT EXISTS idx_fact_event_entity
    ON dw.fact_event (entity_key);

-- -----------------------------------------------------------------------------
-- 4. Snowflake tùy chọn: tách category ra bảng riêng
-- Bỏ comment và thêm FK nếu nhóm chọn snowflake cho nhánh phân cấp này.
-- -----------------------------------------------------------------------------
-- CREATE TABLE IF NOT EXISTS dw.dim_category (
--     category_key   BIGSERIAL   PRIMARY KEY,
--     category_code  VARCHAR(64) NOT NULL UNIQUE,
--     category_name  VARCHAR(100) NOT NULL,
--     parent_code    VARCHAR(64)
-- );

-- -----------------------------------------------------------------------------
-- 5. Truy vấn OLAP mẫu (chạy sau khi ETL đã nạp dữ liệu)
-- Slice: lọc một lát cắt. Dice: lọc nhiều dimension.
-- Roll-up: GROUP BY mức cao hơn. Drill-down: GROUP BY mức thấp hơn.
-- -----------------------------------------------------------------------------

-- Roll-up: doanh số / giá trị theo năm
-- SELECT d.year,
--        SUM(f.amount)   AS total_amount,
--        SUM(f.quantity) AS total_quantity
-- FROM dw.fact_event f
-- JOIN dw.dim_date d ON d.date_key = f.date_key
-- GROUP BY d.year
-- ORDER BY d.year;

-- Slice + dice: theo quý và phân khúc, chỉ lấy năm hiện hành trong dimension
-- SELECT d.quarter,
--        e.segment,
--        SUM(f.amount) AS total_amount
-- FROM dw.fact_event f
-- JOIN dw.dim_date d   ON d.date_key = f.date_key
-- JOIN dw.dim_entity e ON e.entity_key = f.entity_key AND e.is_current
-- WHERE d.year = 2026
-- GROUP BY d.quarter, e.segment
-- ORDER BY d.quarter, total_amount DESC;
