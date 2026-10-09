# PROJECT PLAN — Urban Traffic Flow & Road Safety DW/DSS

> Tài liệu bàn giao và kế hoạch sống của dự án. Agent tiếp quản phải đọc file này trước khi làm việc; cập nhật chính file này khi có thay đổi có ý nghĩa.

- Phiên bản: 0.2.1
- Cập nhật: 2026-10-10 (Asia/Bangkok, UTC+7)
- Trạng thái: S2 xong (profiling tái lập, `reports/profiling/PROFILE.md`); S0 một phần — chưa kiểm tra máy Windows của người dùng.
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
| Hệ điều hành phát triển Windows | Đã chốt bởi người dùng | Chưa biết phiên bản Windows/cấu hình máy |
| Cần có web application về sau | Đã chốt bởi người dùng | Tách ETL khỏi notebook và API |
| Một file kế hoạch được cập nhật liên tục | Đã chốt bởi người dùng | File này là bản bàn giao chính |
| London, 2021–2025 | Phạm vi MVP đề xuất trước đó | Phụ thuộc năm chung và trạng thái bản phát hành; cần xác nhận |
| VS Code + Git + Docker Compose | Đề xuất | Chưa cài đặt hoặc kiểm tra trên máy người dùng |
| PostgreSQL/PostGIS + Python + FastAPI | Đề xuất | Chốt sau kiểm tra tài nguyên và yêu cầu triển khai |
| React + Vite + ECharts + Leaflet | Đề xuất | Frontend cho dashboard và bản đồ |
| DSS bằng MCDA, có thể thêm tối ưu ngân sách | Đề xuất | Ưu tiên mô hình giải thích được |
| Tích hợp địa bàn–năm trước, spatial sau | Đề xuất | Spatial là mở rộng, không chặn MVP nếu thiếu dữ liệu |
| Giữ cây `src/` theo GUIDE.md thay cho cây mục 10 | Đã áp dụng (D06) | Đề yêu cầu nộp `src/database`, `src/etl`, `src/frontend`, `src/dss` |
| Bài toán trong README (KSI/100.000 dân theo highway authority) khác hướng B | **Mâu thuẫn, cần người dùng chốt** (D08) | README chốt 08/10; kế hoạch này ghi hướng B do người dùng chốt. Chưa sửa README |

## 4. Business Problem và Business Questions

**Business Problem đề xuất:** dữ liệu tai nạn và lưu lượng nằm ở các nguồn có grain khác nhau. Nhà quy hoạch cần một cách thống nhất để xem xu hướng, nhận diện địa bàn cần khảo sát và so sánh mức độ ưu tiên đầu tư, đồng thời thấy độ tin cậy và phạm vi bao phủ của dữ liệu.

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
- Trạng thái provisional/final không ghi trong file nào; còn phải đối chiếu trang DfT.

**Trạng thái bằng chứng ban đầu: chưa tái lập.** Hội thoại hiện tại không cung cấp script, log hoặc output gốc xác minh các con số này. Không đưa vào báo cáo như kết quả đã chứng minh. Cần chạy lại profiling và ghi file nguồn, hash, thời gian chạy, filters, kết quả. Đặc biệt kiểm tra năm 2025, định nghĩa collision identifier và bản phát hành provisional/final từ metadata.

### 6.3 Tài liệu môn học

Đã có 10 PDF: Chapter 1; Chapter 2 (hai phần); Chapter 3; Chapter 4; Chapter 5 (hai phần); Chapter 6; Chapter 7; Chapter 8. Nội dung tương ứng nền tảng DW, thiết kế DW, management support, DSS, modeling và development. Tài liệu chưa được đọc lại khi tạo file này; khi trích lý thuyết cần đọc PDF và dẫn trang thực tế.

## 7. Data Integration PoC và các điều kiện chuyển bước

**A. Profiling:** inspect archive/schema, encoding, row counts, keys, duplicates, missing/sentinel values, ranges, coordinates, road class, estimation methods, authority codes, release notes. Giữ raw bất biến và lập source manifest có checksum.

**B. Authority–year integration:** chuẩn hóa code/type; kiểm tra mapping và boundary changes; lọc năm chung. Aggregate collision và AADF độc lập về authority–year, sau đó kết hợp. Không join từng collision với từng count point chỉ bằng authority–year vì sẽ nhân bản measures. Báo coverage và số điểm từng năm; mean AADF cần giải thích là trung bình của mẫu điểm quan sát.

**C. Spatial integration — tùy chọn:** cần road geometry phù hợp, CRS xác định, khóa liên kết link–count point và temporal validity. Major Roads shapefile là ứng viên, chưa đảm bảo bao phủ minor roads. Nearest point không tự chứng minh cùng link. Dùng khoảng cách theo CRS mét, road class/road number nếu phù hợp, kiểm tra thủ công mẫu, lưu match method/distance/confidence/ambiguity. Cho phép unmatched; không ép ghép tất cả.

**Gate trước thiết kế vật lý:** có báo cáo profiling tái lập; key/grain đúng; năm/địa bàn tương thích; mapping contract; KPI đủ dữ liệu; giới hạn exposure được ghi rõ. Nếu C thất bại, tiếp tục MVP A+B và để link-level rates ở trạng thái deferred.

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
| P0 | Kiểm tra Windows version, tài nguyên, WSL2/Docker và công cụ đã có | Pending — người dùng chạy `scripts/check_env.ps1` và dán kết quả |
| P0 | Chốt phạm vi MVP London và năm sau kiểm tra metadata | Pending — chờ profiling và người dùng |
| P0 | Chốt bài toán: README hay hướng B (D08) | Pending — cần người dùng |
| P0 | Lấy đúng ba datasets, inventory và source manifest | Done 2026-10-10 — `data/manifest/source_manifest.json` |
| P1 | Tạo repository và môi trường tái lập | Done một phần — skeleton có; Docker chưa chạy thử |
| P1 | Viết/run profiling | Done 2026-10-10 — `src/etl/profiling.py`, `reports/profiling/` |
| P1 | Authority–year PoC kèm mapping contract | Pending |
| P1 | Đối chiếu trạng thái provisional/final trên trang DfT | Pending |
| P2 | Chốt KPI contract và grain, rồi thiết kế DW | Blocked bởi profiling/PoC |
| P3 | Spatial PoC / link-level rate | Optional; cần geometry và mapping |

Agent tiếp theo nên bắt đầu bằng kiểm tra môi trường Windows và dựng project skeleton, đồng thời kiểm tra dữ liệu có thể truy cập. Không bắt đầu xây frontend hoặc coi các số profiling cũ là đã xác nhận.

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
| D08 | 2026-10-10 | README (08/10) chốt bài toán KSI/100.000 dân; kế hoạch ghi hướng B | Mâu thuẫn mở, cần người dùng chọn hoặc gộp |
| D09 | 2026-10-10 | Mỗi tính năng một branch `cursor/*-b2a4` và một PR vào `main`; các PR xếp chồng, merge theo thứ tự | Người dùng yêu cầu |

## 14. Changelog

| Phiên bản | Ngày | Thay đổi | Evidence |
|---|---|---|---|
| 0.1.0 | 2026-10-09 | Tạo kế hoạch tổng hợp; Windows roadmap; integration gates; KPI/DSS guardrails; next actions | Hội thoại người dùng; chưa kiểm chứng lại datasets |
| 0.2.0 | 2026-10-10 | Đưa kế hoạch vào repo; skeleton S0; source manifest có sha256; ánh xạ cây thư mục (D06); thêm nguồn local authority traffic (D07); ghi mâu thuẫn bài toán (D08) | `data/manifest/source_manifest.json`; 5 unittest; `schema.sql` chạy trên PostgreSQL 16 |
| 0.2.1 | 2026-10-10 | Profiling S2 tái lập; xác nhận 8 con số cũ; ghi phát hiện link length Minor, làm tròn nhóm phương tiện, số dạng khoa học, lệch mã authority | `reports/profiling/PROFILE.md`; 10 unittest |

Mẫu cập nhật cuối phiên: `Ngày — phiên bản — việc hoàn thành — file/log/test minh chứng — quyết định mới — blocker — bước tiếp theo`.
