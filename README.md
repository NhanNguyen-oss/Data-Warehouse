# Traffic Flow & Road Safety DW/DSS — London, 2021–2025

## Description

Bài tập lớn môn **Kho dữ liệu và Hệ hỗ trợ Quyết định** (CO4031), học kỳ 261, năm học 2026–2027.
Giảng viên: Đỗ Thanh Thái. Hạn nộp: **23:59 ngày 15/11/2026**.

Lộ trình chi tiết, yêu cầu của đề và checklist nộp bài nằm trong [`GUIDE.md`](GUIDE.md).

### Thành viên

| Họ tên | MSSV | Vai trò chính |
| --- | --- | --- |
| Vo Dinh Tri | 2313632 | Thiết kế kho dữ liệu, FE, DSS |
| Nguyen Chi Nhan | 2312430 | Kỹ sư dữ liệu (ETL), DSS |

### Bài toán và phạm vi MVP

**Traffic Flow + Road Safety tại London, giai đoạn 2021–2025**, được người dùng chốt ngày 10/10/2026. Hệ thống tích hợp STATS19 và DfT Traffic Counts để phân tích xu hướng tai nạn và lưu lượng, hỗ trợ chuyên viên quy hoạch so sánh mức độ ưu tiên khảo sát hoặc đầu tư theo địa bàn.

- Phạm vi phân tích: 33 London authorities; dữ liệu raw toàn quốc được giữ để truy vết và tái lập.
- Hai nguồn được tổng hợp riêng về authority–year trước khi kết hợp, tránh nhân bản số liệu.
- KPI chính: số vụ, mức độ nghiêm trọng và số hiệu chỉnh, số nạn nhân, AADF tại điểm, tăng trưởng trên tập điểm chung và tỷ lệ bản ghi ước tính.
- DSS dự kiến xếp hạng địa bàn, cho đổi trọng số và giải thích điểm. Công thức và trọng số sẽ được đặc tả ở bước thiết kế.
- Rate trên vehicle-km chưa bật; spatial/link-level analysis là phần mở rộng. Dân số ONS và bài toán chọn 10 địa bàn nhận quỹ toàn quốc nằm ngoài MVP đã chốt.

Xem [`PROJECT_PLAN.md`](PROJECT_PLAN.md) để biết KPI contract, giới hạn phương pháp, quyết định D13 và tiến độ hiện tại. Các mục trạng thái ngày 08/10 bên dưới là lịch sử trước khi chốt MVP này.

### Kiểm chứng backend hiện tại

Ngày 10/10/2026, baseline STATS19 toàn quốc đã được nạp vào container và đối soát khớp: 513.801 vụ, 937.265 xe, 652.821 nạn nhân. Xem [`reports/validation/STATS19_LOAD.md`](reports/validation/STATS19_LOAD.md) và [`src/database/verify_load.sql`](src/database/verify_load.sql). Kết nối host qua `DW_DATABASE_URL` đã được sửa và kiểm chứng; lần nạp baseline dùng psql trong container. London mart và tích hợp Traffic chưa triển khai.

### Dữ liệu

- **Nguồn:** [Road safety open data](https://www.gov.uk/government/statistical-data-sets/road-safety-open-data) của Bộ Giao thông Anh (Department for Transport, DfT), hệ thống ghi nhận STATS19. Dùng bộ "last 5 years", bản dữ liệu chính thức cho năm 2025.
- **Giấy phép:** Open Government Licence v3.0. Được phép dùng lại, kể cả cho mục đích học tập, nếu ghi nguồn.
- **Phạm vi:** các vụ tai nạn giao thông có người bị thương trên đường công cộng tại Anh, xứ Wales và Scotland, được cảnh sát ghi nhận, từ 01/01/2021 đến 31/12/2025.

Các file trong `data/raw/`:

| File | Một dòng là | Số dòng | Số cột |
| --- | --- | --- | --- |
| `dft-road-casualty-statistics-collision-last-5-years.csv` | một vụ va chạm | 513.801 | 44 |
| `dft-road-casualty-statistics-vehicle-last-5-years.csv` | một xe trong một vụ | 937.265 | 32 |
| `dft-road-casualty-statistics-casualty-last-5-years.csv` | một nạn nhân | 652.821 | 24 |
| `dft-road-casualty-statistics-road-safety-open-dataset-data-guide-2025.xlsx` | bảng tra mã sang nhãn (sheet `2024_code_list`) | 1.777 nhãn | — |

Ba bảng nối với nhau qua `collision_index`. Bảng xe và bảng nạn nhân nối thêm qua `vehicle_reference`.

#### Đặc điểm dữ liệu và cách ETL xử lý

- **Liên kết sạch.** Không có xe hay nạn nhân nào trỏ tới vụ không tồn tại, và không có khóa trùng. Cột `number_of_vehicles` và `number_of_casualties` khớp 100% với số dòng chi tiết. ETL dùng hai cột này để đối soát sau mỗi lần chạy.
- **Dữ liệu dạng mã số.** Ví dụ `weather_conditions = 2`. ETL đọc file tra mã chính thức để ghi kèm nhãn (`Raining no high winds`) vào cột `<tên cột>_label` của dimension.
- **`-1` nghĩa là thiếu dữ liệu.** Với cột mã, `-1` được giữ nguyên và gắn nhãn `Data missing or out of range`. Với cột số đo (tuổi, dung tích động cơ, tuổi xe), `-1` được lưu là NULL.
- **Cột bị thay thế.** `local_authority_district` gần như toàn `-1` (513.607 trên 513.801 dòng), nên ETL dùng `local_authority_ons_district`. Các cột có đuôi `_historic` là mã hóa cũ và không được nạp.
- **Hiệu chỉnh mức độ nghiêm trọng.** 309.049 vụ được ghi theo hệ thống báo cáo dựa trên thương tích, làm số ca "nặng" tăng so với cách ghi cũ. DfT cung cấp xác suất đã hiệu chỉnh (`*_adjusted_severity_serious/slight`). Kho lưu cả số gốc và số hiệu chỉnh. Khi so sánh giữa các năm hoặc địa bàn, dùng `KSI hiệu chỉnh = SUM(fatal_count) + SUM(adjusted_serious)`.
- **Mã mới chưa có trong file tra mã 2025.** Gồm 7 mã quận huyện sau tái cơ cấu hành chính (E06000063–E06000066, E08000038, E08000039, E07000246) và `casualty_type = 33`, mã DfT thêm vào bản sửa đổi tháng 9/2026. Các dòng này có nhãn `Code ... (not in data guide)`. Cần bổ sung nhãn khi DfT phát hành file tra mã mới.
- **Mức độ thiếu dữ liệu.** Thiếu nhiều ở `generic_make_model`, `age_of_vehicle`, `engine_capacity_cc` và `driver_distance_banding`. Không nên dùng các cột này làm tiêu chí chính của DSS.

### Mô hình kho dữ liệu

Kho dùng mô hình fact constellation: ba star schema dùng chung các dimension. Chi tiết nằm trong `src/database/schema.sql`.

| Fact | Grain | Measure chính |
| --- | --- | --- |
| `fact_collision` | một vụ va chạm | số xe, số nạn nhân, cờ tử vong / nặng / nhẹ, số hiệu chỉnh, tọa độ |
| `fact_vehicle` | một xe trong một vụ | số xe, tuổi người lái, dung tích động cơ, tuổi xe |
| `fact_casualty` | một nạn nhân | số nạn nhân, cờ tử vong / nặng / nhẹ, số hiệu chỉnh, tuổi nạn nhân |

Các dimension dùng chung: `dim_date`, `dim_time`, `dim_location`, `dim_road`, `dim_conditions`, `dim_severity`.
Các dimension riêng: `dim_vehicle`, `dim_driver`, `dim_vehicle_action`, `dim_casualty`.

View `dw.v_local_authority_year` tổng hợp số vụ, số nạn nhân và KSI hiệu chỉnh theo quận ONS và năm. Đầu vào của DSS sẽ là một view mới ở cấp highway authority (xem mục Việc còn mở).

### Cấu trúc thư mục

```text
.
├── GUIDE.md               # lộ trình và yêu cầu bài tập lớn
├── PROJECT_PLAN.md        # kế hoạch sống, decision log, bàn giao giữa các phiên
├── README.md
├── compose.yaml           # PostgreSQL/PostGIS bằng Docker
├── .env.example           # cấu hình mẫu, chép thành .env (không commit)
├── requirements.txt
├── data/
│   ├── raw/               # 3 file CSV STATS19 và file tra mã của DfT
│   │   └── traffic/       # DfT Traffic Counts, tải bằng sources.py (không commit)
│   ├── manifest/          # source_manifest.json: sha256, kích thước, số dòng
│   ├── reference/         # authority_code_map.csv: mapping contract mã authority
│   ├── staging/           # dữ liệu trung gian (không commit)
│   └── processed/         # CSV do ETL sinh ra, mỗi bảng dw.* một file (không commit)
├── docs/                  # báo cáo PDF và slide PDF
├── reports/profiling/     # PROFILE.md và profile.json do profiling.py sinh ra
├── reports/poc/           # authority_year.csv, remap_audit.csv, RECONCILIATION.md do authority_year.py sinh ra
├── scripts/check_env.ps1  # kiểm tra môi trường Windows (stage S0)
├── scripts/check_db.ps1   # dựng container db và kiểm tra health (stage S0)
├── tests/                 # unittest, chạy bằng python -m unittest discover -s tests
└── src/
    ├── database/schema.sql    # DDL kho dữ liệu, view và truy vấn OLAP mẫu
    ├── etl/sources.py         # danh mục nguồn, tải, manifest có checksum
    ├── etl/profiling.py       # profiling nguồn (S2), ghi reports/profiling/
    ├── etl/authority_year.py  # PoC tích hợp authority x year (S3), ghi reports/poc/
    ├── etl/pipeline.py        # Extract, Transform, Load
    ├── frontend/app.py        # dashboard Streamlit
    └── dss/model.py           # mô hình hỗ trợ quyết định
```

### Trạng thái

Cập nhật ngày 08/10/2026.

`schema.sql` và `pipeline.py` đã viết theo dữ liệu STATS19. `frontend/app.py` và `dss/model.py` vẫn là khung mẫu và đang chạy trên dữ liệu demo.

| Giai đoạn | Nội dung | Hạn | Trạng thái |
| --- | --- | --- | --- |
| 1 | Chốt bài toán, KPI, nguồn dữ liệu | 04/10 | Xong ngày 08/10 (trễ 4 ngày). Còn thiếu mục 1 của báo cáo và nguồn dân số ONS |
| 2 | Schema và ETL | 25/10 | ETL chạy đủ 5 năm ra CSV trong khoảng 1 phút, không loại dòng nào, đối soát khớp. Chưa chạy thử `schema.sql` và `--load` trên PostgreSQL. Chưa có SCD |
| 3 | CSDL, OLAP, dashboard | 01/11 | Đã có view `v_local_authority_year` và 5 truy vấn OLAP mẫu (chưa chạy). Dashboard chưa làm |
| 4 | DSS trên số liệu của kho | 08/11 | Chưa bắt đầu |
| 5 | Đánh giá, hạn chế, hướng phát triển | 12/11 | Chưa bắt đầu |
| 6 | Báo cáo, slide, ZIP, nộp LMS | 15/11 | Chưa bắt đầu |

Kết quả lần chạy ETL đủ 5 năm (kiểm tra lại ngày 08/10):

| Bảng | Số dòng |
| --- | --- |
| `fact_collision` / `fact_vehicle` / `fact_casualty` | 513.801 / 937.265 / 652.821 |
| `dim_location` / `dim_vehicle_action` / `dim_road` / `dim_casualty` | 45.751 / 28.345 / 22.162 / 20.280 |
| `dim_vehicle` / `dim_driver` / `dim_conditions` | 3.002 / 2.073 / 1.949 |
| `dim_date` / `dim_time` / `dim_severity` | 1.826 / 1.441 / 3 |

#### Việc còn mở

1. **Viết mục 1 của báo cáo** từ phần Bài toán ở trên: bối cảnh, người ra quyết định, KPI, nguồn dữ liệu, danh sách cột nguồn.
2. **Tải dân số ONS** (mid-year population estimates 2021–2025, cấp county và unitary authority) vào `data/raw/`, rồi đối chiếu mã với `local_authority_highway_current`.
3. **Bổ sung SCD Type 2 cho highway authority.** Chuẩn đầu ra L.O.2 yêu cầu SCD, nhưng schema hiện chưa có. Thêm bảng `dim_highway_authority` có `effective_from`, `effective_to`, `is_current`, và sửa ETL để đọc thêm cột `local_authority_highway_current` (hiện `dim_location` chỉ lưu mã tại thời điểm xảy ra vụ). Các thay đổi có thật: Cumbria (`E10000006`) tách thành Cumberland (`E06000063`) và Westmorland and Furness (`E06000064`) từ năm 2023; Sheffield (`E08000019` sang `E08000039`) và Barnsley (`E08000016` sang `E08000038`) đổi mã. Khoảng 1.500 dòng lệch lẻ giữa các quận London giống sửa lỗi hơn là đổi địa giới, cần lọc riêng.
4. **Thêm fact dân số** dạng periodic snapshot (một dòng là một highway authority trong một năm). Đây là measure semi-additive: cộng được theo địa bàn, không cộng theo năm.
5. **Viết lại view đầu vào cho DSS** ở cấp highway authority và mức nạn nhân, thay cho `v_local_authority_year` (đang ở cấp quận ONS, mức vụ va chạm và xếp theo số tuyệt đối). View mới tính sẵn bốn tiêu chí trong bảng Mô hình DSS.
6. **Cài PostgreSQL**, chạy `schema.sql`, rồi chạy `python src/etl/pipeline.py --load`. Kiểm tra số dòng trong `dw.*` khớp với bảng trên và chạy thử các truy vấn OLAP mẫu.
7. **Sửa `src/dss/model.py`** để chọn top 10 thay vì một phương án, đọc từ view mới, và in câu giải thích theo tiêu chí.
8. **Viết dashboard** (`src/frontend/app.py`) theo 5 KPI ở trên.
9. **Luôn dùng KSI hiệu chỉnh khi so sánh giữa các năm.** Tỷ lệ vụ được ghi theo hệ thống dựa trên thương tích tăng từ 49,6% (2021) lên 86,5% (2025). KSI gốc tăng 17% trong giai đoạn này, KSI hiệu chỉnh chỉ tăng 12,7%.
10. **Chuẩn bị dữ liệu nộp bài.** Ba file nguồn tổng cộng khoảng 257 MB, riêng file vehicle 104,7 MB (sát giới hạn 100 MiB mỗi file của GitHub). Nên để bản trích (ví dụ năm 2025) trong `data/` và ghi link nguồn DfT trong báo cáo.

## How to use this source code

### Chạy dashboard với PostgreSQL

Kết nối host đã được kiểm chứng với user `dw`, database `road_safety_dw`. Dashboard chạy trực tiếp trên Windows, PostgreSQL chạy trong Docker. URL thực tế nằm trong `.env` (không commit).

Dashboard đọc dữ liệu STATS19 thật từ PostgreSQL cho 33 London authorities, giai đoạn 2021–2025. Bộ lọc năm/địa bàn cập nhật số vụ, số nạn nhân, số tử vong và KSI hiệu chỉnh ở mức nạn nhân. Heathrow được gộp vào Hillingdon. Tích hợp Traffic và DSS chưa triển khai.

1. Dùng `.env` trong root dự án (chép từ `.env.example` nếu chưa có). Đặt `DW_DATABASE_URL` khớp kết nối đã thành công trong công cụ quản lý database:

```dotenv
DW_DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<database>
```

Mật khẩu có ký tự đặc biệt phải URL-encode, ví dụ `@` thành `%40`. Dashboard tự đọc `.env`; biến môi trường `DW_DATABASE_URL` có ưu tiên cao hơn. Không commit mật khẩu.

2. Chạy từ PowerShell tại root repository:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
docker compose up -d db
.venv\Scripts\python.exe src/frontend/warehouse.py
.venv\Scripts\python.exe -m streamlit run src/frontend/app.py
```

3. Mở http://localhost:8501. Chọn năm/địa bàn ở sidebar; dùng **Refresh data** sau khi thay cấu hình hoặc nạp lại kho. Kết quả truy vấn được cache 60 giây. Dashboard báo lỗi khi kết nối thất bại và không thay bằng demo data.

Nếu dùng biến môi trường cũ, có thể xóa override trong PowerShell để dashboard đọc `.env`:

```powershell
Remove-Item Env:DW_DATABASE_URL -ErrorAction SilentlyContinue
```


### Cài đặt và chạy

Cần Python 3.10 trở lên và PostgreSQL 13 trở lên. Bản thân ETL chỉ dùng thư viện chuẩn. Thư viện `psycopg` chỉ cần khi nạp vào CSDL.

```bash
pip install -r requirements.txt
```

Trên Windows, chạy `powershell -ExecutionPolicy Bypass -File scripts\check_env.ps1` để kiểm tra Git, Python, Docker và WSL2, rồi dán kết quả vào mục 12 của [`PROJECT_PLAN.md`](PROJECT_PLAN.md).

Nếu có Docker, có thể dựng PostgreSQL/PostGIS bằng `compose.yaml` thay cho bước `createdb` bên dưới. Lần chạy đầu tiên tự chạy `schema.sql`.

```bash
cp .env.example .env          # sửa mật khẩu trong .env
docker compose up -d db
```

Trên Windows (Docker Desktop đang chạy), `scripts\check_db.ps1` làm các bước trên, chờ container `healthy` rồi in phiên bản PostgreSQL/PostGIS và số bảng trong schema `dw` (kỳ vọng 14). Không cần cài `psql` trên máy; dùng `docker compose exec db psql -U dw -d road_safety_dw`.

Môi trường Python trên Windows (dùng Python 3.13 qua `py`, vì Python 3.10 hết hỗ trợ từ tháng 10/2026):

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Nguồn DfT Traffic Counts không commit vào Git. Tải về `data/raw/traffic/` và kiểm tra sha256 với manifest đã commit:

```bash
python src/etl/sources.py fetch      # tải file còn thiếu, không ghi đè file đã có
python src/etl/sources.py verify     # so sha256 với data/manifest/source_manifest.json
python src/etl/profiling.py          # profiling S2 -> reports/profiling/PROFILE.md (khoảng 15 giây)
python src/etl/authority_year.py     # PoC S3 authority x year -> reports/poc/RECONCILIATION.md (khoảng 10 giây)
python -m unittest discover -s tests
```

Thứ tự chạy:

```bash
# 1. Tạo CSDL và schema kho dữ liệu
createdb road_safety_dw
psql -d road_safety_dw -f src/database/schema.sql

# 2. Chạy ETL: ghi data/processed/*.csv và etl_report.csv (khoảng 2 phút, 175 MB cho đủ 5 năm)
python src/etl/pipeline.py
python src/etl/pipeline.py --years 2025      # chỉ một năm
python src/etl/pipeline.py --limit 5000      # bản nhỏ để thử

# 3. Nạp vào PostgreSQL (PowerShell; trên bash dùng export)
$env:DW_DATABASE_URL = "postgresql://<user>:<password>@localhost:5432/road_safety_dw"
python src/etl/pipeline.py --load

# 4. Mở dashboard
streamlit run src/frontend/app.py

# 5. Chạy mô hình DSS
python src/dss/model.py
```

Mỗi lần chạy `--load`, ETL xóa dữ liệu cũ trong các bảng `dw.*` rồi nạp lại toàn bộ trong một transaction. Chuỗi kết nối đọc từ biến môi trường, không ghi mật khẩu vào mã nguồn. File `.env` đã có trong `.gitignore`.


## Citations

- **Assignment requirements:** [CO4031 assignment guide](GUIDE.md), semester 261, academic year 2026-2027.
- **STATS19 data and codebook:** Department for Transport, [Road safety open data](https://www.gov.uk/government/statistical-data-sets/road-safety-open-data).
- **Traffic data:** Department for Transport, [Road traffic statistics downloads](https://roadtraffic.dft.gov.uk/downloads). Source definitions: [`src/etl/sources.py`](src/etl/sources.py). File versions and checksums: [`data/manifest/source_manifest.json`](data/manifest/source_manifest.json).
- **Data licence:** [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Attribute Department for Transport when reusing its data.
