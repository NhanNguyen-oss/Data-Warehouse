# Kho dữ liệu và Hệ hỗ trợ Quyết định về an toàn giao thông đường bộ (STATS19, Anh 2021–2025)

Bài tập lớn môn **Kho dữ liệu và Hệ hỗ trợ Quyết định** (CO4031), học kỳ 261, năm học 2026–2027.
Giảng viên: Đỗ Thanh Thái. Hạn nộp: **23:59 ngày 15/11/2026**.

Lộ trình chi tiết, yêu cầu của đề và checklist nộp bài nằm trong [`GUIDE.md`](GUIDE.md).

## Thành viên

| Họ tên | MSSV | Vai trò chính |
| --- | --- | --- |
| _(điền)_ | _(điền)_ | Thiết kế kho dữ liệu |
| _(điền)_ | _(điền)_ | Kỹ sư dữ liệu (ETL) |
| _(điền)_ | _(điền)_ | Frontend và DSS |

## Bài toán

> _Chưa chốt._ Viết theo mẫu: *Ai cần quyết định điều gì, dựa trên chỉ số nào, trong kỳ nào?*

Các hướng đang cân nhắc:

1. Xếp hạng quận huyện cần ưu tiên ngân sách an toàn giao thông năm tới (chính quyền địa phương).
2. Chọn khung giờ, loại đường và điều kiện thời tiết để tăng tuần tra hoặc kiểm soát tốc độ (cảnh sát).
3. Chọn nhóm người tham gia giao thông dễ bị tổn thương (đi bộ, xe đạp, xe máy, e-scooter) cho chiến dịch truyền thông.
4. Chọn loại nút giao hoặc mức giới hạn tốc độ cần cải tạo hạ tầng trước.

KPI dự kiến: số vụ, số nạn nhân, **KSI hiệu chỉnh** (số người chết hoặc bị thương nặng, đã hiệu chỉnh) và tỷ lệ KSI trên tổng số vụ. Các KPI này được xem theo địa bàn, thời gian, điều kiện đường và loại phương tiện.

## Dữ liệu

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

### Đặc điểm dữ liệu và cách ETL xử lý

- **Liên kết sạch.** Không có xe hay nạn nhân nào trỏ tới vụ không tồn tại, và không có khóa trùng. Cột `number_of_vehicles` và `number_of_casualties` khớp 100% với số dòng chi tiết. ETL dùng hai cột này để đối soát sau mỗi lần chạy.
- **Dữ liệu dạng mã số.** Ví dụ `weather_conditions = 2`. ETL đọc file tra mã chính thức để ghi kèm nhãn (`Raining no high winds`) vào cột `<tên cột>_label` của dimension.
- **`-1` nghĩa là thiếu dữ liệu.** Với cột mã, `-1` được giữ nguyên và gắn nhãn `Data missing or out of range`. Với cột số đo (tuổi, dung tích động cơ, tuổi xe), `-1` được lưu là NULL.
- **Cột bị thay thế.** `local_authority_district` gần như toàn `-1` (513.607 trên 513.801 dòng), nên ETL dùng `local_authority_ons_district`. Các cột có đuôi `_historic` là mã hóa cũ và không được nạp.
- **Hiệu chỉnh mức độ nghiêm trọng.** 309.049 vụ được ghi theo hệ thống báo cáo dựa trên thương tích, làm số ca "nặng" tăng so với cách ghi cũ. DfT cung cấp xác suất đã hiệu chỉnh (`*_adjusted_severity_serious/slight`). Kho lưu cả số gốc và số hiệu chỉnh. Khi so sánh giữa các năm hoặc địa bàn, dùng `KSI hiệu chỉnh = SUM(fatal_count) + SUM(adjusted_serious)`.
- **Mã mới chưa có trong file tra mã 2025.** Gồm 7 mã quận huyện sau tái cơ cấu hành chính (E06000063–E06000066, E08000038, E08000039, E07000246) và `casualty_type = 33`, mã DfT thêm vào bản sửa đổi tháng 9/2026. Các dòng này có nhãn `Code ... (not in data guide)`. Cần bổ sung nhãn khi DfT phát hành file tra mã mới.
- **Mức độ thiếu dữ liệu.** Thiếu nhiều ở `generic_make_model`, `age_of_vehicle`, `engine_capacity_cc` và `driver_distance_banding`. Không nên dùng các cột này làm tiêu chí chính của DSS.

## Mô hình kho dữ liệu

Kho dùng mô hình fact constellation: ba star schema dùng chung các dimension. Chi tiết nằm trong `src/database/schema.sql`.

| Fact | Grain | Measure chính |
| --- | --- | --- |
| `fact_collision` | một vụ va chạm | số xe, số nạn nhân, cờ tử vong / nặng / nhẹ, số hiệu chỉnh, tọa độ |
| `fact_vehicle` | một xe trong một vụ | số xe, tuổi người lái, dung tích động cơ, tuổi xe |
| `fact_casualty` | một nạn nhân | số nạn nhân, cờ tử vong / nặng / nhẹ, số hiệu chỉnh, tuổi nạn nhân |

Các dimension dùng chung: `dim_date`, `dim_time`, `dim_location`, `dim_road`, `dim_conditions`, `dim_severity`.
Các dimension riêng: `dim_vehicle`, `dim_driver`, `dim_vehicle_action`, `dim_casualty`.

View `dw.v_local_authority_year` tổng hợp số vụ, số nạn nhân và KSI hiệu chỉnh theo quận huyện và năm. View này là đầu vào cho dashboard và DSS.

## Cấu trúc thư mục

```text
.
├── GUIDE.md               # lộ trình và yêu cầu bài tập lớn
├── README.md
├── data/
│   ├── raw/               # 3 file CSV STATS19 và file tra mã của DfT
│   └── processed/         # CSV do ETL sinh ra, mỗi bảng dw.* một file (không commit)
├── docs/                  # báo cáo PDF và slide PDF
└── src/
    ├── database/schema.sql    # DDL kho dữ liệu, view và truy vấn OLAP mẫu
    ├── etl/pipeline.py        # Extract, Transform, Load
    ├── frontend/app.py        # dashboard Streamlit
    └── dss/model.py           # mô hình hỗ trợ quyết định
```

## Cài đặt và chạy

Cần Python 3.10 trở lên và PostgreSQL 13 trở lên. Bản thân ETL chỉ dùng thư viện chuẩn. Thư viện `psycopg` chỉ cần khi nạp vào CSDL.

```bash
pip install "psycopg[binary]" streamlit pandas
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

## Trạng thái

`schema.sql` và `pipeline.py` đã viết theo dữ liệu STATS19. `frontend/app.py` và `dss/model.py` vẫn là khung mẫu và đang chạy trên dữ liệu demo.

| Giai đoạn | Nội dung | Hạn | Trạng thái |
| --- | --- | --- | --- |
| 1 | Chốt bài toán, KPI, nguồn dữ liệu | 04/10 | Đã chọn và khảo sát dữ liệu, chưa chốt bài toán |
| 2 | Schema và ETL | 25/10 | ETL chạy đủ 5 năm ra CSV, đối soát khớp; chưa chạy thử nạp PostgreSQL |
| 3 | CSDL, OLAP, dashboard | 01/11 | Chưa bắt đầu |
| 4 | DSS trên số liệu của kho | 08/11 | Chưa bắt đầu |
| 5 | Đánh giá, hạn chế, hướng phát triển | 12/11 | Chưa bắt đầu |
| 6 | Báo cáo, slide, ZIP, nộp LMS | 15/11 | Chưa bắt đầu |
