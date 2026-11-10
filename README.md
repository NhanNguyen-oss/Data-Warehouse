# Traffic Flow & Road Safety DW/DSS — London, 2021–2025

Bài tập lớn môn **Kho dữ liệu và Hệ hỗ trợ Quyết định** (CO4031), học kỳ 261, năm học 2026–2027. Giảng viên: Đỗ Thanh Thái. Hạn nộp: **23:59 ngày 15/11/2026**. Yêu cầu của đề và checklist nộp bài nằm trong [`GUIDE.md`](GUIDE.md); KPI contract, decision log và tiến độ nằm trong [`PROJECT_PLAN.md`](PROJECT_PLAN.md).

| Họ tên | MSSV | Vai trò chính |
| --- | --- | --- |
| Vo Dinh Tri | 2313632 | Thiết kế kho dữ liệu, FE, DSS |
| Nguyen Chi Nhan | 2312430 | Kỹ sư dữ liệu (ETL), DSS |

## Giới thiệu

Hệ thống tích hợp STATS19 và DfT Traffic Counts để phân tích xu hướng tai nạn và lưu lượng tại **33 London authorities, giai đoạn 2021–2025**, giúp chuyên viên quy hoạch so sánh mức độ ưu tiên khảo sát hoặc đầu tư theo địa bàn.

- **KPI chính:** số vụ, mức độ nghiêm trọng và số hiệu chỉnh, số nạn nhân, AADF tại điểm, tăng trưởng trên tập điểm chung, tỷ lệ bản ghi ước tính. Hai nguồn được tổng hợp riêng về authority–year trước khi kết hợp để tránh nhân bản số liệu.
- **Ngoài phạm vi MVP:** rate trên vehicle-km, phân tích spatial/link-level (phần mở rộng), dân số ONS và bài toán chọn 10 địa bàn nhận quỹ toàn quốc.
- **Dữ liệu:** [Road safety open data](https://www.gov.uk/government/statistical-data-sets/road-safety-open-data) (STATS19, bộ "last 5 years") của Bộ Giao thông Anh (DfT), giấy phép Open Government Licence v3.0. Gồm vụ va chạm (513.801 dòng), xe (937.265) và nạn nhân (652.821) có người bị thương tại Anh, xứ Wales và Scotland, cùng file tra mã (1.777 nhãn). Ba bảng nối qua `collision_index`; xe và nạn nhân nối thêm qua `vehicle_reference`. Dữ liệu raw toàn quốc được giữ để truy vết; baseline đã nạp và đối soát khớp ([`STATS19_LOAD.md`](reports/validation/STATS19_LOAD.md)).

### Cách ETL xử lý dữ liệu

- Đối soát `number_of_vehicles` và `number_of_casualties` với số dòng chi tiết sau mỗi lần chạy (hiện khớp 100%, không có khóa trùng hay khóa mồ côi).
- Ghi kèm nhãn từ file tra mã vào cột `<tên cột>_label`. Mã chưa có trong file tra mã 2025 (7 mã quận sau tái cơ cấu và `casualty_type = 33`) được gắn nhãn `Code ... (not in data guide)`.
- `-1` nghĩa là thiếu dữ liệu: giữ nguyên ở cột mã (nhãn `Data missing or out of range`), lưu NULL ở cột số đo (tuổi, dung tích động cơ, tuổi xe).
- Dùng `local_authority_ons_district` thay cho `local_authority_district` (gần như toàn `-1`); không nạp các cột `_historic`.
- Lưu cả số gốc và số hiệu chỉnh mức độ nghiêm trọng do DfT cung cấp. **Khi so sánh giữa các năm hoặc địa bàn, luôn dùng `KSI hiệu chỉnh = SUM(fatal_count) + SUM(adjusted_serious)`**, vì tỷ lệ vụ ghi theo hệ thống dựa trên thương tích tăng từ 49,6% (2021) lên 86,5% (2025).
- Các cột thiếu nhiều (`generic_make_model`, `age_of_vehicle`, `engine_capacity_cc`, `driver_distance_banding`) không dùng làm tiêu chí DSS.

### Mô hình kho dữ liệu

Fact constellation gồm ba star schema dùng chung dimension ([`schema.sql`](src/database/schema.sql)):

| Fact | Grain | Measure chính |
| --- | --- | --- |
| `fact_collision` | một vụ va chạm | số xe, số nạn nhân, cờ tử vong / nặng / nhẹ, số hiệu chỉnh, tọa độ |
| `fact_vehicle` | một xe trong một vụ | số xe, tuổi người lái, dung tích động cơ, tuổi xe |
| `fact_casualty` | một nạn nhân | số nạn nhân, cờ tử vong / nặng / nhẹ, số hiệu chỉnh, tuổi nạn nhân |

Dimension dùng chung: `dim_date`, `dim_time`, `dim_location`, `dim_road`, `dim_conditions`, `dim_severity`. Dimension riêng: `dim_vehicle`, `dim_driver`, `dim_vehicle_action`, `dim_casualty`.

### Cấu trúc thư mục

```text
├── compose.yaml, .env.example, requirements.txt
├── data/        raw/ (STATS19, traffic/), manifest/, reference/, staging/, processed/
├── docs/        báo cáo và slide
├── reports/     profiling/, poc/, validation/
├── scripts/     check_env.ps1, check_db.ps1
├── tests/       unittest
└── src/
    ├── database/  schema.sql, verify_load.sql
    ├── etl/       sources.py, profiling.py, authority_year.py, pipeline.py
    ├── frontend/  app.py (Streamlit), dss_panel.py, warehouse.py
    └── dss/       model.py, authority.py, run.py
```

`data/raw/traffic/`, `data/staging/`, `data/processed/` và `.env` không được commit.

## Cách vận hành

Cần Python 3.10+ (khuyến nghị 3.13), Docker Desktop (PostgreSQL/PostGIS) và PowerShell tại root repository.

**1. Kiểm tra môi trường và cài thư viện.** `check_env.ps1` kiểm tra Git, Python, Docker và WSL2.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_env.ps1
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**2. Cấu hình kết nối.** Chép `.env.example` thành `.env`, sửa mật khẩu và đặt:

```dotenv
DW_DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<database>
```

Ký tự đặc biệt trong mật khẩu phải URL-encode (ví dụ `@` thành `%40`). Biến môi trường `DW_DATABASE_URL` được ưu tiên hơn `.env`; xóa bằng `Remove-Item Env:DW_DATABASE_URL` nếu muốn dùng `.env`.

**3. Dựng PostgreSQL.** Lần chạy đầu tiên tự chạy `schema.sql`. `check_db.ps1` dựng container, chờ `healthy` rồi in phiên bản và số bảng trong schema `dw` (kỳ vọng 14). Mở psql bằng `docker compose exec db psql -U dw -d road_safety_dw`.

```powershell
docker compose up -d db
powershell -ExecutionPolicy Bypass -File scripts\check_db.ps1
```

**4. Chuẩn bị nguồn, ETL và nạp kho.** `--load` xóa dữ liệu cũ trong `dw.*` rồi nạp lại toàn bộ trong một transaction.

```powershell
python src/etl/sources.py fetch      # tải DfT Traffic Counts còn thiếu vào data/raw/traffic/
python src/etl/sources.py verify     # so sha256 với data/manifest/source_manifest.json
python src/etl/profiling.py          # -> reports/profiling/PROFILE.md
python src/etl/authority_year.py     # PoC authority x year -> reports/poc/RECONCILIATION.md
python src/etl/pipeline.py           # ghi data/processed/*.csv (khoảng 2 phút cho đủ 5 năm)
python src/etl/pipeline.py --years 2025   # hoặc --limit 5000 để chạy thử
python src/etl/pipeline.py --load    # nạp vào PostgreSQL
python src/frontend/warehouse.py     # kiểm tra kết nối và số liệu London
```

**5. Mở dashboard** tại http://localhost:8501:

```powershell
python -m streamlit run src/frontend/app.py
```

- **Bảng điều khiển BI:** số vụ, số nạn nhân, số tử vong, KSI hiệu chỉnh ở mức nạn nhân, biểu đồ theo tháng và theo địa bàn, bảng chi tiết và tải CSV. Heathrow được gộp vào Hillingdon.
- **Hỗ trợ ra quyết định:** xếp hạng địa bàn cần ưu tiên khảo sát an toàn giao thông. Đổi trọng số của KSI hiệu chỉnh trung bình năm, thay đổi KSI và tỷ trọng KSI (mặc định thăm dò 50/30/20, tự chuẩn hóa); chọn ngưỡng điểm và số địa bàn đề xuất; xem đóng góp từng tiêu chí, lý do đề xuất, so sánh what-if với trọng số mặc định và tải CSV kết quả.
- Bộ lọc năm/địa bàn ở sidebar áp dụng cho cả hai trang. Chọn một năm sẽ tắt tiêu chí xu hướng; địa bàn thiếu tháng hoặc thiếu số hiệu chỉnh bị loại kèm lý do. Điểm chỉ phản ánh ưu tiên tương đối trong tập đang chọn.
- Truy vấn được cache 60 giây; bấm **Làm mới dữ liệu** sau khi đổi cấu hình hoặc nạp lại kho. Khi kết nối lỗi, dashboard báo lỗi và không thay bằng dữ liệu demo. Dữ liệu Traffic chưa được tích hợp vào dashboard.

**6. Chạy DSS từ CLI và test.** Công thức, giả định và kết quả kiểm chứng DSS nằm trong [`reports/validation/DSS.md`](reports/validation/DSS.md).

```powershell
python src/dss/model.py --years 2021 2022 2023 2024 2025 --top 5
python src/dss/model.py --weights 0 100 0 --top 5
python -m unittest discover -s tests
```

## Citations

- **Assignment requirements:** [CO4031 assignment guide](GUIDE.md), semester 261, academic year 2026-2027.
- **STATS19 data and codebook:** Department for Transport, [Road safety open data](https://www.gov.uk/government/statistical-data-sets/road-safety-open-data).
- **Traffic data:** Department for Transport, [Road traffic statistics downloads](https://roadtraffic.dft.gov.uk/downloads). Source definitions: [`src/etl/sources.py`](src/etl/sources.py). File versions and checksums: [`data/manifest/source_manifest.json`](data/manifest/source_manifest.json).
- **Data licence:** [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Attribute Department for Transport when reusing its data.
