# PROJECT PLAN — Urban Traffic Flow & Road Safety DW/DSS

> Tài liệu bàn giao và kế hoạch sống của dự án. Agent tiếp quản phải đọc file này trước khi làm việc; cập nhật chính file này khi có thay đổi có ý nghĩa.

- Phiên bản: 0.3.7
- Cập nhật: 2026-10-10 (Asia/Bangkok, UTC+7)
- Trạng thái: S2 và S3 (authority–year) xong, đối soát khớp raw; S3 spatial chưa làm (optional). S0 xong trên máy Windows của người dùng (Docker Desktop, PostgreSQL 16.4 + PostGIS 3.4.3 healthy, schema `dw` 14 bảng/view). S1 đã chốt London 2021–2025, Traffic Flow + Road Safety (D13); Baseline STATS19 đã nạp và đối soát trong container qua psql; host dashboard đã nối DB thật sau sửa authentication; host ETL `--load` chưa chạy lại. S4 sẵn sàng thiết kế London mart.
- Repository: https://github.com/NhanNguyen-oss/Data-Warehouse
- Người dùng: đang dùng Windows; muốn xây dựng Assignment có thể phát triển thành web.
- Ngôn ngữ làm việc: tiếng Việt; giữ thuật ngữ kỹ thuật bằng tiếng Anh.
- Tên dự án đề xuất: `urban-traffic-dw-dss`.

## 1. Hướng dẫn cho agent tiếp quản

1. Đọc toàn bộ file; xác định bước hiện tại ở mục 12.
2. Phân biệt **đã chốt**, **đề xuất**, **chưa kiểm chứng**. Không biến đề xuất thành yêu cầu đã được người dùng duyệt.
3. Kiểm tra repository, môi trường và dữ liệu thực tế trước khi triển khai. Không coi đoạn hội thoại trước là bằng chứng một lệnh đã chạy hoặc một tính năng đã hoàn thành.
4. Sau mỗi thay đổi về scope, kiến trúc, schema, KPI, nguồn dữ liệu, kết quả kiểm chứng hoặc milestone: sửa các mục liên quan, cập nhật phiên bản/ngày và thêm một dòng changelog.
5. Khi kết thúc phiên, ghi việc đã làm, bằng chứng, blocker và bước tiếp theo. Nếu chưa thực hiện, ghi rõ Planned; không ghi Done.
6. Giữ một file kế hoạch chính. Khi file đã có danh tính lưu trữ, cập nhật cùng file thay vì tạo nhiều bản `final`, `final2`. Khi có repository, đưa bản kế hoạch này vào root và commit cùng thay đổi liên quan.
7. Nếu kết quả mới phủ định thông tin cũ, sửa trạng thái hiện tại và lưu lý do trong changelog/decision log.
8. Không ghi mật khẩu, token, chuỗi kết nối có secret hoặc dữ liệu nhạy cảm vào file.

Quy tắc phiên bản: patch cho cập nhật tiến độ; minor cho thay đổi thiết kế/phạm vi; major khi đổi hướng bài toán. Việc cập nhật cần được thực hiện bởi agent đang làm việc; file không tự đồng bộ với mọi cuộc hội thoại.

## 2. Mục tiêu và criteria của Assignment

**Assignment requirements:** [`GUIDE.md`](GUIDE.md) defines the CO4031 assignment requirements, learning outcomes, deliverables, submission deadline and assessment checklist. This project plan translates those requirements into implementation tasks; consult the guide when changing scope or preparing the submission.

Xây dựng hệ thống tích hợp dữ liệu giao thông và tai nạn để phân tích theo thời gian/địa bàn, hỗ trợ ưu tiên khảo sát và đầu tư hạ tầng đô thị.

| Criterion | Sản phẩm cần có | Bằng chứng hoàn thành |
|---|---|---|
| 1. Phân tích nghiệp vụ | Business Problem, Questions, KPI, scope, data requirements | Định nghĩa KPI và ma trận câu hỏi–dữ liệu |
| 2. Thiết kế DW + ETL | Grain, fact/dimension, star/snowflake, mapping nguồn–đích | ERD, data dictionary, ETL specification |
| 3. Backend + frontend | Database, pipeline, OLAP, API, dashboard | Chạy end-to-end trên dữ liệu thật; truy vấn và demo |
| 4. Thành phần DSS | Ranking, thay đổi trọng số, so sánh kịch bản | Công thức, giả định, kết quả và sensitivity analysis |
| 5. Đánh giá | Data quality, correctness, hiệu năng, hạn chế | Test report, đối chiếu số liệu, hướng phát triển |

DW phục vụ dữ liệu phân tích; dashboard trình bày kết quả; DSS bổ sung mô hình để so sánh và hỗ trợ lựa chọn phương án.

## 3. Các quyết định và trạng thái

| Nội dung | Trạng thái | Ghi chú |
|---|---|---|
| Hướng B: Traffic Flow + Road Safety | Đã chốt bởi người dùng | Tích hợp STATS19 và DfT Traffic Counts |
| Hệ điều hành phát triển Windows | Đã chốt bởi người dùng | Windows 11 Pro build 26300, 31,8 GB RAM, 356 GB trống (mục 12, phiên 0.3.1) |
| Windows host + Docker Desktop (WSL2 backend), Python 3.13 venv | Đã áp dụng (D12) | Docker Compose v5.5.1 và WSL2 đã có; container chưa chạy thử |
| Cần có web application về sau | Đã chốt bởi người dùng | Tách ETL khỏi notebook và API |
| Một file kế hoạch được cập nhật liên tục | Đã chốt bởi người dùng | File này là bản bàn giao chính |
| London, 2021–2025 | Đã chốt bởi người dùng 2026-10-10 (D13) | MVP Traffic Flow + Road Safety; 33 London authorities; giữ raw toàn quốc |
| VS Code + Git + Docker Compose | Đề xuất | Chưa cài đặt hoặc kiểm tra trên máy người dùng |
| PostgreSQL/PostGIS + Python + FastAPI | Đề xuất | Chốt sau kiểm tra tài nguyên và yêu cầu triển khai |
| React + Vite + ECharts + Leaflet | Đề xuất | Frontend cho dashboard và bản đồ |
| DSS bằng MCDA, có thể thêm tối ưu ngân sách | Đề xuất | Ưu tiên mô hình giải thích được; trọng số/công thức chưa chốt |
| Tích hợp địa bàn–năm trước, spatial sau | Đề xuất | Spatial là mở rộng, không chặn MVP nếu thiếu dữ liệu |
| Giữ cây `src/` theo GUIDE.md thay cho cây mục 10 | Đã áp dụng (D06) | Đề yêu cầu nộp `src/database`, `src/etl`, `src/frontend`, `src/dss` |
| Bài toán chính: Traffic Flow + Road Safety tại London | Đã chốt 2026-10-10 (D13); đóng D08 | Xếp hạng địa bàn bằng chỉ số tai nạn và lưu lượng; dân số và bài toán quỹ toàn quốc nằm ngoài MVP |

## 4. Business Problem và Business Questions

**Business Problem cho MVP đã chốt (D13):** dữ liệu tai nạn và lưu lượng nằm ở các nguồn có grain khác nhau. Nhà quy hoạch cần một cách thống nhất để xem xu hướng, nhận diện địa bàn cần khảo sát và so sánh mức độ ưu tiên đầu tư, đồng thời thấy độ tin cậy và phạm vi bao phủ của dữ liệu.

Đối tượng sử dụng giả định: chuyên viên quy hoạch, phân tích giao thông và quản lý hạ tầng. Đây là mô hình học thuật, chưa được xác thực qua phỏng vấn stakeholder.

| ID | Câu hỏi nghiệp vụ | Dữ liệu/điều kiện |
|---|---|---|
| BQ1 | Số vụ và mức độ nghiêm trọng thay đổi ra sao theo địa bàn, năm? | Collision + severity + authority + date |
| BQ2 | Lưu lượng tại các điểm/link được quan sát thay đổi ra sao? | AADF + count point/link + year; kiểm tra thay đổi độ bao phủ |
| BQ3 | Địa bàn nào có đồng thời nhiều tai nạn nghiêm trọng và lưu lượng cao? | Aggregate hai nguồn riêng rồi kết hợp authority–year |
| BQ4 | Link nào có tỷ lệ tai nạn cao so với exposure? | Chỉ mở khi spatial match và denominator cùng phạm vi được kiểm chứng |
| BQ5 | Có khác biệt theo road class, điều kiện đường/thời tiết? | STATS19 coded fields; metadata và missing codes |
| BQ6 | Ưu tiên địa bàn/link nào khi đổi trọng số hoặc ngân sách? | DSS score; chi phí chỉ dùng khi có nguồn hoặc giả định công khai |

Không dùng dữ liệu AADF theo năm để kết luận về tắc nghẽn giờ cao điểm hay tốc độ thời gian thực. STATS19 không đại diện cho mọi va chạm/near-miss chưa được ghi nhận.

## 5. KPI contract đề xuất

Mỗi KPI phải có grain, công thức, đơn vị, nguồn, bộ lọc, quy tắc missing và phạm vi diễn giải.

| KPI | Công thức/ý nghĩa | Ràng buộc |
|---|---|---|
| Recorded collisions | COUNT DISTINCT collision identifier | Theo bộ lọc năm/địa bàn |
| Fatal/serious collisions | Đếm vụ có severity tương ứng | Là số vụ; không gọi là số người chết/bị thương nặng |
| Severe collision share | (Fatal + serious collisions) / all collisions × 100% | Thiếu/không rõ severity phải có quy tắc riêng |
| Casualties | SUM số người bị nạn nếu có trường phù hợp | KSI persons cần casualty-level severity; collision severity không thay thế được |
| AADF tại điểm/link | Lưu lượng trung bình ngày trong năm theo metadata nguồn | Vehicles/day; không cộng mọi điểm để gọi là lưu lượng toàn thành phố |
| AADF growth | (AADF năm t / AADF năm t−1 − 1) × 100% | So cùng điểm hoặc tập điểm chung; mẫu số 0 trả NULL |
| Estimated share | Số bản ghi ước tính / tổng AADF records × 100% | Theo phương pháp và phạm vi được lọc |
| Vehicle-km/year | AADF × link_length_km × số ngày của năm | Chỉ link hợp lệ, không double-count; xử lý leap year |
| Collisions/100 million vehicle-km | Collisions / vehicle-km × 100,000,000 | Tử và mẫu cùng mạng đường/năm; chưa được bật mặc định |
| Spatial match coverage | Matched eligible collisions / eligible collisions × 100% | Báo riêng unmatched, ambiguous, bị loại |
| Priority score | Tổng trọng số × tiêu chí đã chuẩn hóa | Tách score khỏi confidence; không phải dự báo hiệu quả đầu tư |

Trong MVP authority–year, trình bày hai nhóm chỉ số cạnh nhau. Không tính rate bằng tất cả tai nạn địa bàn chia cho exposure chỉ của một phần mạng đường.

Ràng buộc bổ sung từ profiling (v0.2.1): Vehicle-km từ AADF chỉ khả thi cho Major roads (Minor thiếu `link_length_km` 100%). Severe collision share cần cờ injury-based hoặc số hiệu chỉnh `collision_adjusted_severity_*` khi so sánh giữa các năm. AADF growth phải so trên tập count point có mặt ở cả hai năm (21.201 điểm có mặt cả 5 năm toàn quốc, 1.977 ở London).

## 6. Nguồn dữ liệu và evidence ledger

### 6.1 Dữ liệu đã được nhắc đến trong hội thoại

| File | Danh tính đã biết | Vai trò |
|---|---|---|
| dft-road-casualty-statistics-collision-last-5-years.csv | libfile_3ede761dd52081918f8f41980f9cab90 | Collision events |
| dft_traffic_counts_aadf.zip | libfile_59ef6c7cf7908191b6c9939ee30d1d1e | AADF theo count point–year |
| count_points.zip | libfile_d6c45faa9d4c8191932cd3e40a66bd33 | Metadata count points |

Nguồn tham chiếu:
- Road Safety Open Data: https://www.gov.uk/government/statistical-data-sets/road-safety-open-data
- DfT Traffic Downloads: https://roadtraffic.dft.gov.uk/downloads

Ba file dữ liệu trên có danh tính trong lịch sử nhưng chưa được đọc/kiểm chứng trong phiên tạo kế hoạch này. Khi làm profiling phải lấy đúng file hiện tại; không giả định chúng đã có trong workspace của agent mới.

### 6.1b Nguồn đang dùng trong repository (2026-10-10)

Danh sách đầy đủ, sha256, kích thước và số bản ghi nằm trong `data/manifest/source_manifest.json`, sinh bằng `python src/etl/sources.py manifest`. Kiểm tra máy khác bằng `python src/etl/sources.py verify`. STATS19 đã có sẵn trong `data/raw/`. Ba nguồn Traffic được tải bằng `sources.py fetch` vào `data/raw/traffic/` và không commit.

| source_id | File | sha256 (12 ký tự đầu) | Bản ghi CSV |
|---|---|---|---|
| stats19_collision | dft-road-casualty-statistics-collision-last-5-years.csv | 06a03c0e5504 | 513.801 |
| stats19_vehicle | dft-road-casualty-statistics-vehicle-last-5-years.csv | 05453dca2651 | 937.265 |
| stats19_casualty | dft-road-casualty-statistics-casualty-last-5-years.csv | 870be5a934ae | 652.821 |
| stats19_data_guide | …data-guide-2025.xlsx | 51b08606ef3d | (codebook) |
| traffic_aadf | traffic/dft_traffic_counts_aadf.zip (member ngày 2026-06-02) | 5273cf63da4c | 600.551 |
| traffic_count_points | traffic/count_points.zip (member ngày 2026-06-02) | 4772abb13761 | 46.754 |
| traffic_local_authority | traffic/local_authority_traffic.csv | 058a61b9f6f7 | 6.767 |

`local_authority_traffic.csv` là nguồn mới so với v0.1.0: vehicle miles ước tính theo local authority × year cho toàn mạng đường (major và minor). Đây là ứng viên exposure cùng phạm vi với tổng tai nạn của địa bàn (D07). Chưa bật rate cho đến khi profiling xác nhận định nghĩa và độ bao phủ.

Các file DfT trên Google Cloud Storage có thể được thay bằng bản phát hành mới mà không đổi tên. Vì vậy `verify` báo lệch sha256 là dấu hiệu cần chạy lại profiling, không tự ghi đè manifest.

### 6.2 Những kết quả cũ cần tái kiểm chứng

Assistant trước đã báo cáo: 513.801 collisions; 600.551 AADF rows; 46.754 count points; London 111.335 collisions và 10.207 AADF rows; 33/33 authority codes khớp; 64,5% estimated AADF; 22,43% thiếu link length toàn quốc.

**Cập nhật 2026-10-10 (v0.2.1):** đã tái lập bằng `python src/etl/profiling.py` trên các file có sha256 ở mục 6.1b. Kết quả đầy đủ trong `reports/profiling/profile.json` và `PROFILE.md`.

| Con số cũ | Kết quả tái lập | Ghi chú |
|---|---|---|
| 513.801 collisions | Khớp | `collision_index` duy nhất, 0 trùng; 2021–2025 |
| 600.551 AADF rows | Khớp | Năm 2000–2025; khóa (`count_point_id`, `year`) 0 trùng |
| 46.754 count points | Khớp | 0 trùng; mọi count point AADF đều có metadata |
| London 111.335 collisions | Khớp | Định nghĩa: `local_authority_highway` bắt đầu bằng `E09`, 2021–2025 |
| London 10.207 AADF rows | Khớp | `local_authority_code` bắt đầu bằng `E09`, 2021–2025; trùng khớp `region_name = London` |
| 33/33 authority codes khớp | Khớp | Cả ba nguồn, mọi năm 2021–2025 |
| 64,5% estimated AADF | Khớp cho London (64,54%) | Toàn quốc 2021–2025 là 64,38% |
| 22,43% thiếu link length toàn quốc | Khớp cho toàn file 2000–2025 | 2021–2025 là 19,73%; **Minor roads thiếu 100%**, Major 0% |

Phát hiện mới có ảnh hưởng thiết kế:
- AADF chỉ có `link_length_km` cho Major roads, nên vehicle-km tính từ AADF chỉ phủ mạng Major. Rate theo toàn bộ tai nạn địa bàn phải dùng `local_authority_traffic.csv` (D07) hoặc lọc tai nạn theo road class tương ứng.
- 49.297 dòng AADF có tổng nhóm phương tiện lệch `all_motor_vehicles` ±1 hoặc ±2 (làm tròn). ETL phải dùng `all_motor_vehicles` của nguồn, không cộng nhóm.
- `local_authority_traffic.csv` có 1.318 dòng ghi số dạng khoa học (`1.245e+09`); phải parse bằng float.
- Mã authority: so với AADF và LA traffic, `local_authority_highway` (mã lúc xảy ra vụ) khớp tốt hơn `_current`. Lệch còn lại: `EHEATHROW`; Sheffield/Barnsley mã mới `E08000039`/`E08000038` trong STATS19 2025 so với mã cũ `E08000019`/`E08000016` bên Traffic; Cumbria `E10000006` còn trong AADF 2023; `E10000021` (Northamptonshire) trong AADF 2021. Cần mapping contract ở S3.
- Tỷ lệ vụ ghi theo injury-based tăng từ 49,62% (2021) lên 86,53% (2025), nên severe collision share không so sánh được giữa các năm nếu không hiệu chỉnh.
- (v0.3.0) Cờ `collision_injury_based` không đáng tin làm chỉ báo: Metropolitan Police có cờ 0 cho 2021–2024 (chỉ ~20 vụ/năm có cờ 1) và 1 cho 2025, nhưng serious hiệu chỉnh bằng serious gốc ở mọi năm. Một phần mức tăng toàn quốc ở trên là do Met đổi cờ năm 2025. Dùng `collision_adjusted_severity_*` thay cho cờ (D11).
- Trạng thái provisional/final không ghi trong file nào; còn phải đối chiếu trang DfT.

**Trạng thái bằng chứng ban đầu: chưa tái lập.** Hội thoại hiện tại không cung cấp script, log hoặc output gốc xác minh các con số này. Không đưa vào báo cáo như kết quả đã chứng minh. Cần chạy lại profiling và ghi file nguồn, hash, thời gian chạy, filters, kết quả. Đặc biệt kiểm tra năm 2025, định nghĩa collision identifier và bản phát hành provisional/final từ metadata.

### 6.3 Tài liệu môn học

Đã có 10 PDF: Chapter 1; Chapter 2 (hai phần); Chapter 3; Chapter 4; Chapter 5 (hai phần); Chapter 6; Chapter 7; Chapter 8. Nội dung tương ứng nền tảng DW, thiết kế DW, management support, DSS, modeling và development. Tài liệu chưa được đọc lại khi tạo file này; khi trích lý thuyết cần đọc PDF và dẫn trang thực tế.

## 7. Data Integration PoC và các điều kiện chuyển bước

**A. Profiling:** inspect archive/schema, encoding, row counts, keys, duplicates, missing/sentinel values, ranges, coordinates, road class, estimation methods, authority codes, release notes. Giữ raw bất biến và lập source manifest có checksum.

**B. Authority–year integration:** chuẩn hóa code/type; kiểm tra mapping và boundary changes; lọc năm chung. Aggregate collision và AADF độc lập về authority–year, sau đó kết hợp. Không join từng collision với từng count point chỉ bằng authority–year vì sẽ nhân bản measures. Báo coverage và số điểm từng năm; mean AADF cần giải thích là trung bình của mẫu điểm quan sát.

**C. Spatial integration — tùy chọn:** cần road geometry phù hợp, CRS xác định, khóa liên kết link–count point và temporal validity. Major Roads shapefile là ứng viên, chưa đảm bảo bao phủ minor roads. Nearest point không tự chứng minh cùng link. Dùng khoảng cách theo CRS mét, road class/road number nếu phù hợp, kiểm tra thủ công mẫu, lưu match method/distance/confidence/ambiguity. Cho phép unmatched; không ép ghép tất cả.

**Gate trước thiết kế vật lý:** có báo cáo profiling tái lập; key/grain đúng; năm/địa bàn tương thích; mapping contract; KPI đủ dữ liệu; giới hạn exposure được ghi rõ. Nếu C thất bại, tiếp tục MVP A+B và để link-level rates ở trạng thái deferred.

**Kết quả A+B (2026-10-10, v0.3.0).** Chạy `python src/etl/authority_year.py`; bằng chứng ở `reports/poc/RECONCILIATION.md`, `authority_year.csv` (1.033 dòng = 207 authority × 5 năm, trừ biến động địa giới) và `remap_audit.csv`.

| Điều kiện gate | Trạng thái | Bằng chứng |
|---|---|---|
| Profiling tái lập | Đạt | `reports/profiling/` có run_id và sha256 |
| Key/grain đúng | Đạt | collision_index, (count_point_id, year), (local_authority_code, year) đều duy nhất; output 0 khóa trùng |
| Năm/địa bàn tương thích | Đạt | Năm chung 2021–2025; 1.033/1.033 authority–year của LA traffic có mặt; London 33/33 |
| Mapping contract | Đạt | `data/reference/authority_code_map.csv` (3 quy tắc) + quy tắc `count_point_later_code` (11 dòng AADF); 0 collision và 0 AADF row không ghép được |
| Đối soát với raw | Đạt | Collisions 513.801 = 513.801; AADF 111.465 = 111.465; LA traffic 1.033 = 1.033; Major vehicle-km AADF không vượt vehicle-km toàn mạng ở authority–year nào |
| KPI đủ dữ liệu | Đạt một phần | Đủ cho collisions, severity, adjusted KSI, AADF điểm, estimated share. Rate chỉ ở dạng `candidate_*` |
| Giới hạn exposure ghi rõ | Đạt | Mục Phương pháp và Giới hạn trong `RECONCILIATION.md` |
| Phạm vi MVP được người dùng chốt | Đạt 2026-10-10 | D13: London, 2021–2025; PoC toàn quốc có tập con London 33/33 |

Mapping contract (D10): mã chuẩn là mã authority mà DfT Traffic dùng trong năm đó. Collision lấy `local_authority_highway` (mã lúc xảy ra vụ) rồi áp bảng ánh xạ: `EHEATHROW` → `E09000017`; `E08000038` → `E08000016` và `E08000039` → `E08000019` (Traffic vẫn dùng mã cũ của Barnsley/Sheffield). AADF có mã không hợp lệ trong năm lấy mã của cùng count point ở năm sau gần nhất (Cumbria 2023: 10 dòng; Northamptonshire 2021: 1 dòng). Cumbria 2021–2022 giữ `E10000006`, nên chuỗi thời gian gãy tại 2023; cần `dim_authority` có version history khi thiết kế S4.

Hai rate thử nghiệm có trong PoC nhưng chưa bật (D05): `candidate_collisions_per_100m_vkm` (tổng collision / vehicle-km toàn mạng của LA traffic, cùng phạm vi mạng đường) và `candidate_major_collisions_per_100m_major_vkm` (collision có `first_road_class` Motorway/A(M)/A chia cho vehicle-km Major từ AADF). London: 77,92 (2021) giảm còn 66,09 (2025) collisions / 100 triệu vehicle-km toàn mạng.

## 8. Kiến trúc và mô hình dữ liệu đề xuất

Luồng: nguồn → raw/staging → ETL validation/transform → PostgreSQL DW → OLAP views → FastAPI → React dashboard/DSS. ETL chạy độc lập với request API.

| Thành phần | Grain/ý nghĩa |
|---|---|
| fact_collision | Một collision event; date/time, authority, severity, điều kiện, số vehicles/casualties nếu có |
| fact_traffic_aadf | Một count point × year, nếu composite key được xác minh; lưu totals và nhóm phương tiện |
| dim_date / dim_year | Dimension thời gian và năm chung, đảm bảo join theo năm không tạo fan-out |
| dim_authority | Authority code chuẩn; version history khi thay đổi có ảnh hưởng |
| dim_count_point | Vị trí và metadata; xử lý thuộc tính thay đổi theo thời gian sau profiling |
| dim_road / dim_road_link | Chỉ xây link dimension khi khóa/geometry được chứng minh |
| dim_severity / dim_conditions | Giải mã coded fields bằng codebook chính thức |
| spatial_match audit/bridge | Collision–link mapping, confidence, trạng thái và version thuật toán |
| mart_authority_year | Kết quả aggregate an toàn cho dashboard, không thay thế hai fact gốc |

Ưu tiên hai star schemas chia sẻ conformed dimensions. Chưa coi đây là ERD cuối cùng. Spatial candidates có thể nhiều; phải có quy tắc chọn/weight trước khi cộng KPI. Không cộng nhóm phương tiện cùng cột tổng dẫn đến đếm hai lần.

ETL cần có run_id, source fingerprint, row counts, reject/quarantine reasons, upsert/idempotency, transaction và log. Phân biệt cập nhật bản phát hành nguồn với lưu lịch sử dimension; không áp dụng SCD Type 2 máy móc cho mọi bảng.

## 9. Lộ trình phát triển trên Windows

Chưa thao tác trên máy Windows của người dùng. Những bước dưới đây là checklist triển khai, không phải trạng thái đã cài.

| Stage | Ý nghĩa | Deliverable / điều kiện hoàn thành |
|---|---|---|
| S0. Environment | Môi trường tái lập | VS Code, Git, Python, Docker/WSL2 nếu hỗ trợ; lệnh version và container health check thành công |
| S1. Business scope | Xây đúng bài toán | Chốt London/năm, BQ, KPI, mandatory vs optional |
| S2. Profiling | Biết dữ liệu thực sự có gì | Script + manifest + quality report, không dựa con số trong chat |
| S3. Integration PoC | Chứng minh nguồn nối được | Authority–year output + reconciliation; spatial riêng nếu đủ dữ liệu |
| S4. DW/ETL design | Chốt grain và mapping | ERD, dictionary, DDL draft, source–target mapping |
| S5. DW implementation | Có backend dữ liệu hoạt động | Migrations, ETL load, keys/FK, rerun không nhân bản |
| S6. OLAP/API | Cung cấp phân tích nhất quán | Slice/dice/drill-down phù hợp; API khớp SQL chuẩn |
| S7. Dashboard | Người dùng xem và truy vấn được | Year/authority filters, trends, maps, coverage/estimated labels |
| S8. DSS | So sánh phương án | Ranking + weight controls + scenario comparison + giải thích score |
| S9. Evaluation/handover | Chứng minh hệ thống và giới hạn | Test/performance report, demo, báo cáo theo 5 criteria, hướng dẫn chạy |

S0 chi tiết: kiểm tra phiên bản Windows, RAM/disk, virtualization/WSL2; chọn chạy toàn bộ trong WSL2 hoặc Windows host + Docker và ghi quyết định. Đề xuất WSL2 + Docker Desktop nếu máy hỗ trợ. Nếu không hỗ trợ Docker, đánh giá cài PostgreSQL/PostGIS trực tiếp.

Sau đó clone/init repository, tạo Python virtual environment, khóa dependencies, tạo `.env.example`, cấu hình DB volume và migrations. Kiểm tra `git --version`, `python --version`, `docker version`, `docker compose version`, `wsl --status` trên máy người dùng. Chọn phiên bản runtime/package từ tài liệu chính thức tại thời điểm triển khai; không mặc định bản latest.

## 10. Tổ chức repository dự kiến

| Đường dẫn | Vai trò |
|---|---|
| PROJECT_PLAN.md | Kế hoạch chính, decision log, handoff |
| README.md | Cài đặt/chạy/demo |
| data/raw, data/staging, data/processed | Dữ liệu theo lớp; không commit file lớn |
| notebooks/ | Exploration, gọi logic module |
| etl/extract, etl/transform, etl/spatial, etl/load | Pipeline Python có CLI |
| warehouse/migrations, warehouse/olap | Schema và truy vấn/view |
| backend/api, backend/dss | REST API và DSS engine |
| frontend/ | React dashboard |
| tests/ | Kiểm chứng dữ liệu và logic |
| docs/, reports/ | Dictionary, thiết kế, evidence, report |
| compose.yaml, .env.example | Service definitions và config mẫu |

Git ignore: secrets, virtual environments, dữ liệu lớn, build artifacts. Ghi hướng dẫn lấy dữ liệu và hash thay vì commit toàn bộ datasets.

**Cây thực tế (D06).** GUIDE.md quy định cây nộp bài `src/database`, `src/etl`, `src/frontend`, `src/dss`, nên giữ cây đó và ánh xạ như sau. Khi có FastAPI/React thì thêm `src/api` và `frontend/`.

| Mục 10 | Repository hiện tại |
|---|---|
| etl/extract | `src/etl/sources.py` (danh mục, tải, manifest) và hàm `extract` trong `src/etl/pipeline.py` |
| etl/transform, etl/load | `src/etl/pipeline.py` |
| warehouse/migrations, warehouse/olap | `src/database/schema.sql` |
| backend/dss | `src/dss/model.py` |
| data/raw, data/staging, data/processed | như mục 10, thêm `data/manifest/` (commit) và `data/raw/traffic/` (không commit) |
| tests/ | `tests/`, dùng `unittest` của thư viện chuẩn |
| compose.yaml, .env.example | root |
| scripts/ | `scripts/check_env.ps1` cho S0 trên Windows |

## 11. DSS và đánh giá

MVP DSS đề xuất: xếp hạng địa bàn để ưu tiên khảo sát bằng MCDA. Người dùng thay trọng số cho mức độ nghiêm trọng, xu hướng tai nạn và lưu lượng trong phạm vi quan sát. Tiêu chí rate chỉ dùng khi exposure hợp lệ. Định nghĩa normalization, hướng tốt/xấu, outliers, missing; weights không âm và tổng chuẩn hóa bằng 1.

Hiển thị đóng góp từng tiêu chí, năm dữ liệu, coverage và tỷ lệ estimated; kiểm tra độ ổn định ranking khi thay trọng số. Ghi rõ đây là ưu tiên khảo sát, chưa là kết luận một dự án đầu tư sẽ giảm bao nhiêu tai nạn.

Mở rộng budget optimization chỉ sau khi có candidate interventions và cost/benefit được xác thực hoặc dữ liệu giả định được ghi nhãn. What-if dùng giả định không được diễn giải thành causal effect hay dự báo đã kiểm chứng.

Kiểm chứng bắt buộc: aggregate đối chiếu raw; không fan-out; FK/orphan/missing; idempotent rerun; zero denominators; leap years; estimated method; API/filter consistency; DSS normalization/tie/missing; spatial sample nếu có. Benchmark các truy vấn đại diện trên cấu hình ghi rõ, rồi đặt target hiệu năng phù hợp thay vì tuyên bố đạt tốc độ chưa đo.

Hạn chế phải đánh giá: under-reporting, annual granularity, coverage/boundary changes, estimated counts, missing link length, spatial mismatch, provisional revisions, thiếu cost/capacity/speed và dữ liệu chứng minh causal impact.

## 12. Trạng thái hiện tại và next actions

**Phiên 0.1.0:** tổng hợp kế hoạch/bàn giao từ hội thoại; ghi Windows; phân biệt đề xuất với kết quả chưa tái lập. Không có cài đặt môi trường, profiling, schema hay code ứng dụng nào được thực hiện.

**Phiên 0.2.0 (cloud agent Linux, không phải máy người dùng):**
- Đưa kế hoạch vào root repository.
- Thêm `src/etl/sources.py`: danh mục 7 nguồn, `fetch` (không ghi đè raw), `manifest` (sha256, bytes, số bản ghi), `verify`. Đã chạy cả bốn lệnh; `verify` khớp.
- Thêm `compose.yaml` (PostGIS 16-3.4, healthcheck, init bằng `schema.sql`), `.env.example`, `requirements.txt`, `scripts/check_env.ps1`, `data/staging/`, `tests/`.
- Bằng chứng: `python -m unittest discover -s tests` qua 5 test. `schema.sql` chạy không lỗi trên PostgreSQL 16 (cài bằng apt trên máy agent). **Chưa kiểm chứng:** `docker compose up` (máy agent không có Docker) và `check_env.ps1` (cần Windows).

**Phiên 0.2.1:** thêm `src/etl/profiling.py` (stage S2). Chạy trên 4 nguồn trong 13,6 giây, ghi `reports/profiling/profile.json` và `PROFILE.md` kèm run_id, sha256 và bộ lọc năm. Kết quả và phát hiện ở mục 6.2. Bằng chứng: 10 unittest qua (thêm 5 test profiling dùng dữ liệu tự tạo).

| Ưu tiên | Việc tiếp theo | Trạng thái |
|---|---|---|
| P0 | Kiểm tra Windows version, tài nguyên, WSL2/Docker và công cụ đã có | Done 2026-10-10 — kết quả ở phiên 0.3.1 |
| P0 | Container health check trên máy Windows | Done 2026-10-10 — `check_db.ps1` trên máy người dùng: healthy, PostgreSQL 16.4, PostGIS 3.4.3, `dw` 14 bảng/view |
| P0 | Chốt phạm vi MVP London và năm sau kiểm tra metadata | Done 2026-10-10 — người dùng chọn London, 2021–2025 (D13) |
| P0 | Chốt bài toán: README hay hướng B (D08) | Done 2026-10-10 — Traffic Flow + Road Safety (D13) |
| P0 | Lấy đúng ba datasets, inventory và source manifest | Done 2026-10-10 — `data/manifest/source_manifest.json` |
| P1 | Tạo repository và môi trường tái lập | Done 2026-10-10 — skeleton, manifest, Docker Compose chạy trên máy người dùng |
| P1 | Nạp STATS19 vào container: `python src/etl/pipeline.py --load` từ `.venv` Python 3.13, đối chiếu số dòng `dw.*` với README | Baseline Done 2026-10-10 qua container psql; host `--load` lỗi authentication. Xem `reports/validation/STATS19_LOAD.md` |
| P1 | Viết/run profiling | Done 2026-10-10 — `src/etl/profiling.py`, `reports/profiling/` |
| P1 | Authority–year PoC kèm mapping contract | Done 2026-10-10 — `src/etl/authority_year.py`, `reports/poc/` |
| P2 | Thiết kế DW S4: `fact_traffic_aadf`, `dim_count_point`, `dim_authority` (SCD2 cho Cumbria), `mart_authority_year`; ERD, dictionary, mapping nguồn–đích | Ready — D13 chốt London 2021–2025; dùng PoC làm bằng chứng thiết kế |
| P2 | Quyết định có bật rate theo LA traffic (D07) | Pending — cần người dùng duyệt phương pháp |
| P1 | Đối chiếu trạng thái provisional/final trên trang DfT | Pending |
| P2 | Chốt KPI contract và grain, rồi thiết kế DW | Unblocked — D13 chốt phạm vi; công thức và trọng số DSS vẫn cần đặc tả |
| P3 | Spatial PoC / link-level rate | Optional; cần geometry và mapping |

**Phiên 0.3.0:** thêm `src/etl/authority_year.py` (stage S3, phần A+B) và `data/reference/authority_code_map.csv`. Chạy toàn quốc 2021–2025 trong 8,7 giây; mọi kiểm tra đối soát đạt (mục 7). Bằng chứng: 16 unittest qua (thêm 6 test cho mapping, aggregate, leap year, không fan-out).

**Phiên 0.3.1 — kết quả `scripts/check_env.ps1` trên máy người dùng (2026-10-10):**

| Mục | Giá trị | Đánh giá |
|---|---|---|
| Windows | 11 Pro, build 26300 | Hỗ trợ WSL2 và Docker Desktop |
| RAM / disk | 31,8 GB / 356,1 GB trống | Đủ cho PostgreSQL và ~300 MB dữ liệu nguồn |
| Virtualization | `False` | Không chặn: Windows trả `VirtualizationFirmwareEnabled = False` khi hypervisor (WSL2/Hyper-V) đã chiếm VT-x. WSL2 đang chạy distro `docker-desktop` nên virtualization hoạt động. Script đã thêm dòng `HypervisorPresent` để rõ hơn |
| git | 2.52.0 | Đủ |
| python | 3.10.11 (`python`), 3.13.13 (`py`) | Repo cần ≥ 3.10, nhưng 3.10 hết hỗ trợ tháng 10/2026; dùng `py -3.13 -m venv .venv` |
| docker | client có; dòng server trống | Docker Desktop chưa chạy lúc kiểm tra (server không phản hồi). Script đã tách client/engine |
| docker compose | v5.5.1 | Đủ |
| psql | Không có | Không cần; dùng `docker compose exec db psql` |
| VS Code | 1.118.1 | Đủ |
| WSL | default `docker-desktop`, version 2 | Chưa có distro Linux riêng; không cần cho phương án D12 |

Lần chạy `scripts\check_db.ps1` đầu tiên trên máy người dùng: `db health healthy`, nhưng ba truy vấn psql không trả gì và script dừng ở `$tables.Trim()` (null). Nguyên nhân: Windows PowerShell 5.1 bỏ dấu nháy kép lồng trong đối số truyền cho chương trình ngoài, nên lệnh `sh -c '... "$POSTGRES_USER" ... "select ..."'` tới psql bị vỡ. Bản sửa truyền SQL qua stdin, dùng `ON_ERROR_STOP` và báo lỗi rõ khi truy vấn không có kết quả. Đã chạy bản sửa end-to-end trên máy agent (Docker 29.1.3, PowerShell 7.4.6): `healthy`, PostgreSQL 16.4, PostGIS 3.4.3, 14 bảng/view trong `dw`. Chạy lại trên máy người dùng (Windows PowerShell, sau khi merge PR #5): `db health healthy`, `PostgreSQL 16.4 (Debian 16.4-1.pgdg110+2)`, `postgis 3.4.3`, `dw tables 14`. S0 đạt điều kiện hoàn thành của mục 9 (lệnh version và container health check thành công).

Quyết định D12: chạy Windows host + Docker Desktop (WSL2 backend) cho PostgreSQL/PostGIS; ETL và test chạy bằng Python 3.13 trong `.venv` trên Windows (mã chỉ dùng thư viện chuẩn và `pathlib`, không phụ thuộc hệ điều hành). Không cần cài distro Ubuntu trong WSL. Thêm `scripts/check_db.ps1` để hoàn tất S0.

Agent tiếp theo: D13 đã chốt Traffic Flow + Road Safety tại London, 2021–2025. Baseline STATS19 đã nạp qua container psql, row count và aggregate khớp (xem `reports/validation/STATS19_LOAD.md`). Bước tiếp theo: S4 (ERD, dictionary, DDL cho phần Traffic và London mart) dựa trên `reports/poc/`; host `DW_DATABASE_URL` đã sửa ở v0.3.7; kiểm chứng lại host ETL khi tự động hóa load. Dashboard STATS19 đã được người dùng yêu cầu nối DB trong phiên 0.3.6; Traffic mart và DSS chưa triển khai. Không bật rate `candidate_*` khi chưa được duyệt.

Ghi chú lịch sử (v0.1.0): agent tiếp theo nên bắt đầu bằng kiểm tra môi trường Windows và dựng project skeleton, đồng thời kiểm tra dữ liệu có thể truy cập. Không bắt đầu xây frontend hoặc coi các số profiling cũ là đã xác nhận.

## 13. Decision log

| ID | Ngày | Quyết định / đề xuất | Lý do / trạng thái |
|---|---|---|---|
| D01 | Trước 2026-10-09 | Người dùng chọn Traffic Flow + Road Safety | Đã chốt trong hội thoại |
| D02 | 2026-10-09 | Môi trường người dùng Windows | Người dùng xác nhận |
| D03 | 2026-10-09 | Dùng một PROJECT_PLAN.md để bàn giao/cập nhật | Người dùng yêu cầu |
| D04 | 2026-10-09 | Hai fact riêng, tích hợp aggregate trước | Đề xuất; tránh nhân bản measures |
| D05 | 2026-10-09 | Chưa bật exposure-normalized rate nếu chưa kiểm chứng | Guardrail phương pháp; cần cùng coverage |
| D06 | 2026-10-10 | Giữ cây `src/` của GUIDE.md, ánh xạ cây mục 10 vào đó | Áp dụng; đề yêu cầu cây nộp bài cố định |
| D07 | 2026-10-10 | Thêm `local_authority_traffic.csv` làm ứng viên exposure toàn mạng đường | Đề xuất; chưa bật rate (giữ D05) |
| D08 | 2026-10-10 | README (08/10) chốt bài toán KSI/100.000 dân; kế hoạch ghi hướng B | Đã giải quyết bằng D13: chọn hướng B, London 2021–2025 |
| D09 | 2026-10-10 | Mỗi tính năng một branch `cursor/*-b2a4` và một PR vào `main`; các PR xếp chồng, merge theo thứ tự | Người dùng yêu cầu |
| D10 | 2026-10-10 | Mã authority chuẩn = mã DfT Traffic trong năm; collision dùng mã lúc xảy ra vụ + bảng ánh xạ; AADF dùng `count_point_later_code` | Áp dụng trong PoC; đối soát 0 dòng không ghép được |
| D11 | 2026-10-10 | Không dùng cờ `collision_injury_based` làm chỉ báo; dùng số hiệu chỉnh | Bằng chứng: Met Police 2021–2024 |
| D12 | 2026-10-10 | Windows host + Docker Desktop (WSL2 backend); Python 3.13 venv qua `py`; psql trong container | Áp dụng; `check_db.ps1` xác nhận trên máy người dùng 2026-10-10. Không cần cài PostgreSQL native |
| D13 | 2026-10-10 | MVP Traffic Flow + Road Safety, London, 2021–2025 | Người dùng chọn rõ trong phiên này; đóng D08. Rate vẫn chưa bật; spatial tùy chọn; dữ liệu dân số ngoài MVP |

## 14. Changelog

| Phiên bản | Ngày | Thay đổi | Evidence |
|---|---|---|---|
| 0.1.0 | 2026-10-09 | Tạo kế hoạch tổng hợp; Windows roadmap; integration gates; KPI/DSS guardrails; next actions | Hội thoại người dùng; chưa kiểm chứng lại datasets |
| 0.2.0 | 2026-10-10 | Đưa kế hoạch vào repo; skeleton S0; source manifest có sha256; ánh xạ cây thư mục (D06); thêm nguồn local authority traffic (D07); ghi mâu thuẫn bài toán (D08) | `data/manifest/source_manifest.json`; 5 unittest; `schema.sql` chạy trên PostgreSQL 16 |
| 0.2.1 | 2026-10-10 | Profiling S2 tái lập; xác nhận 8 con số cũ; ghi phát hiện link length Minor, làm tròn nhóm phương tiện, số dạng khoa học, lệch mã authority | `reports/profiling/PROFILE.md`; 10 unittest |
| 0.3.0 | 2026-10-10 | Authority–year PoC (S3 A+B); mapping contract (D10); gate trước thiết kế vật lý đạt về dữ liệu, còn chờ chốt phạm vi; cờ injury-based không đáng tin (D11) | `reports/poc/RECONCILIATION.md`; 16 unittest |
| 0.3.1 | 2026-10-10 | Ghi cấu hình máy Windows; chọn môi trường D12; sửa `check_env.ps1` (hypervisor, docker engine); thêm `check_db.ps1` | Output `check_env.ps1` do người dùng gửi; `check_db.ps1` chưa chạy |
| 0.3.2 | 2026-10-10 | Container `healthy` trên máy người dùng; sửa lỗi quoting PowerShell 5.1 trong `check_db.ps1` | Output người dùng gửi; chạy end-to-end trên máy agent: healthy, PG 16.4, PostGIS 3.4.3, 14 bảng/view |
| 0.3.3 | 2026-10-10 | S0 hoàn thành trên máy người dùng | Output `check_db.ps1` người dùng gửi: healthy, PG 16.4, PostGIS 3.4.3, `dw tables 14` |
| 0.3.4 | 2026-10-10 | Reference GUIDE.md as the assignment requirements; restructure README into Description, How to use this source code and Citations | User request; `GUIDE.md`, `README.md` |

| 0.3.5 | 2026-10-10 | Chốt MVP London 2021–2025, Traffic Flow + Road Safety (D13), đóng D08; đồng bộ README; tạo Python 3.13 venv và kiểm chứng CSV ETL | Người dùng chọn phạm vi; 16 unittest pass; ETL CSV 513.801 vụ / 937.265 xe / 652.821 nạn nhân, đối soát khớp; database đã COMMIT qua container psql; `src/database/verify_load.sql` tất cả kiểm tra đạt; `reports/validation/STATS19_LOAD.md` |

| 0.3.6 | 2026-10-10 | Dashboard PostgreSQL cho London: aggregate riêng collision/casualty, bộ lọc năm/địa bàn, CSV; đọc DW_DATABASE_URL từ environment hoặc .env; báo lỗi không lộ secret | 22 unittest pass; SQL container: 1.980 groups, 33 authorities, 111.454 collisions, 128.035 casualties, 486 fatalities, 0 missing adjustment. Host URL hiện vẫn lỗi; chờ người dùng đồng bộ cấu hình với kết nối đã thành công |

| 0.3.7 | 2026-10-10 | Sửa authentication: đồng bộ role password theo cấu hình container, cập nhật URL trong .env không commit; người dùng xác nhận DBeaver với dw/road_safety_dw; dashboard Windows nối DB thật | 23 tests pass; host query 1.980 groups; live AppTest: 111.454 collisions, 128.035 casualties, 486 fatalities, KSI 18.981,9; HTTP localhost:8501 trả 200. Docker-dashboard build thử đã dừng, cấu hình thử được gỡ |

Mẫu cập nhật cuối phiên: `Ngày — phiên bản — việc hoàn thành — file/log/test minh chứng — quyết định mới — blocker — bước tiếp theo`.
