# Hướng dẫn thực hiện bài tập lớn CO4031

Môn **Kho dữ liệu và Hệ hỗ trợ Quyết định** — mã học phần **CO4031**, học kỳ **261** (2026–2027).  
Tỷ trọng: **35%** tổng điểm. Giảng viên: Đỗ Thanh Thái.  
Tài liệu gốc: quy định bài tập lớn phát hành ngày 10/09/2026.

Tài liệu này là lộ trình làm việc cho nhóm **2–3 sinh viên**, bám sáu mục tiêu của đề và hạn nộp **23:59 ngày 15/11/2026**.

## 1. Mục tiêu cần đạt

1. Phân tích yêu cầu nghiệp vụ và xác định bài toán cần giải quyết.
2. Thiết kế kho dữ liệu đa chiều (star schema hoặc snowflake schema), kèm quy trình ETL.
3. Hiện thực hệ thống: backend (cơ sở dữ liệu, ETL, OLAP) và frontend (dashboard hoặc giao diện truy vấn).
4. Phát triển một thành phần hệ hỗ trợ quyết định dựa trên kho dữ liệu đã xây.
5. Đánh giá kết quả, nêu hạn chế và hướng phát triển.
6. Trình bày kết quả trước lớp hoặc bằng video. Mọi thành viên đều phải trình bày.

Kho dữ liệu là **cốt lõi**. Thành phần DSS đọc số liệu đã tích hợp trong kho, không quyết định trực tiếp trên file nguồn hay CSDL tác nghiệp.

### Chuẩn đầu ra mà bài tập lớn phủ

| Chuẩn | Nhóm cần thể hiện ở đâu |
| --- | --- |
| L.O.1.1 – L.O.1.3 | Mở đầu báo cáo: khái niệm DW, vai trò của DW trong DSS, bài toán thực tế của nhóm |
| L.O.2.1 – L.O.2.3 | Thiết kế grain, fact, dimension, SCD và ETL chạy được |
| L.O.3.1 – L.O.3.3 | DSS: đặc tính hệ thống, các giai đoạn ra quyết định, mô hình hóa |
| L.O.4.1 – L.O.4.2 | Phân tích, thiết kế và hiện thực một DSS đơn giản có đầu ra giải thích được |

## 2. Cấu trúc thư mục nộp bài

```text
.
├── GUIDE.md
├── data/                  # dữ liệu mẫu
│   ├── raw/               # nguồn đầu vào của ETL
│   └── processed/         # đầu ra trung gian (CSV) trước khi có CSDL
├── docs/                  # báo cáo PDF và slide PDF
└── src/
    ├── database/schema.sql
    ├── etl/pipeline.py
    ├── frontend/app.py
    └── dss/model.py
```

File ZIP cuối cùng gồm bốn thành phần bắt buộc:

1. Báo cáo PDF (đặt trong `docs/`).
2. Mã nguồn trong `src/` (SQL, Python hoặc R, frontend, ETL). Ưu tiên kho GitHub mà giảng viên truy cập được.
3. Dữ liệu mẫu trong `data/`, hoặc link Google Drive nếu bộ đầy đủ quá lớn.
4. Slide PDF (đặt trong `docs/`).

Nhóm trình bày bằng video: thêm link YouTube (chế độ unlisted) hoặc Google Drive **trên trang bìa báo cáo**.

## 3. Phân công

Mỗi người một vai trò chính, ghi rõ trong báo cáo (họ tên, MSSV, việc đã làm). Điểm cá nhân có thể được cộng hoặc trừ theo đóng góp thực tế, dựa trên peer review và phần trình bày.

Mọi người đều tham gia thuyết trình. Người không trình bày có thể bị trừ điểm cá nhân hoặc không được tính điểm bài tập lớn.

### Nhóm 3 người

| Vai trò | Việc chính | File chịu trách nhiệm |
| --- | --- | --- |
| Thiết kế kho dữ liệu | Grain, star/snowflake, SCD, câu OLAP | `src/database/schema.sql`, sơ đồ trong báo cáo |
| Kỹ sư dữ liệu | Nguồn, làm sạch, nạp kho, đối soát số liệu | `src/etl/pipeline.py`, `data/` |
| Frontend và DSS | Dashboard, mô hình ra quyết định, giải thích kết quả | `src/frontend/app.py`, `src/dss/model.py` |

Viết báo cáo và slide là việc chung. Người phụ trách mục nào viết mục đó, một người soát thể thức.

### Nhóm 2 người

| Người | Gộp vai trò |
| --- | --- |
| Người A | Phân tích nghiệp vụ, thiết kế kho, ETL |
| Người B | OLAP, dashboard, DSS, phần đánh giá trong báo cáo |

Cả hai vẫn cùng soát schema và cùng đứng trình bày.

### Cách ghi nhận đóng góp

Cuối mỗi giai đoạn, ghi 5–10 dòng: ai làm gì, kết quả nằm ở file nào, việc còn mở. Peer review cuối kỳ bám vào nhật ký này, tránh chia điểm theo cảm tính.

## 4. Lộ trình sáu giai đoạn

Học kỳ bắt đầu 24/08/2026 và kết thúc 06/12/2026. Hạn nộp báo cáo là **Chủ nhật 15/11/2026, 23:59** (cuối tuần 12). Thuyết trình diễn ra các tuần 13–15 (19/11, 26/11 và 03/12).

Vì khung này được dựng ở tuần 6, lịch bên dưới nén phần thiết kế (đã học ở tuần 4–5) vào hai tuần đầu của lộ trình.

| Giai đoạn | Việc | Mốc đề xuất |
| --- | --- | --- |
| 1 | Chốt bài toán, KPI, nguồn dữ liệu | 28/09 – 04/10 (tuần 6) |
| 2 | Schema và ETL chạy hết một vòng | 05/10 – 25/10 (tuần 7 và tuần 9; tuần 8 là nghỉ giữa kỳ) |
| 3 | CSDL, OLAP, dashboard | 26/10 – 01/11 (tuần 10) |
| 4 | DSS trên số liệu của kho | 02/11 – 08/11 (tuần 11) |
| 5 | Đánh giá, hạn chế, hướng phát triển | 09/11 – 12/11 |
| 6 | Báo cáo, slide, ZIP, nộp LMS | xong trước 23:59 ngày 15/11/2026 |

Tuần 8 (12/10 – 18/10) là nghỉ giữa kỳ. Nhóm có thể dùng tuần này để nạp dữ liệu, không xếp việc mới bắt buộc.

### Giai đoạn 1 — Phân tích yêu cầu và xác định bài toán

**Mục tiêu.** Chọn một quyết định cụ thể mà kho dữ liệu sẽ hỗ trợ. Đề tài do nhóm tự chọn.

Điều kiện tối thiểu của đề:

- Có kho dữ liệu làm cốt lõi, phục vụ phân tích và ra quyết định.
- Dữ liệu từ nguồn mở (Kaggle, UCI, open data), hoặc dữ liệu doanh nghiệp khi đã được chủ dữ liệu đồng ý, quy mô đủ để aggregate có nghĩa.
- Giải quyết một bài toán trong một lĩnh vực rõ.

Gợi ý lĩnh vực trong đề (không bắt buộc): bán lẻ, ngân hàng, y tế, giáo dục, logistics, thương mại điện tử, nông nghiệp, viễn thông, giao thông đô thị.

**Việc cần làm**

1. Viết một câu bài toán theo mẫu: *Ai cần quyết định điều gì, dựa trên chỉ số nào, trong kỳ nào?*
2. Liệt kê 3–5 câu hỏi phân tích (KPI) mà dashboard phải trả lời được.
3. Liệt kê thực thể, sự kiện và nguồn dữ liệu. Ghi giấy phép hoặc điều kiện sử dụng dữ liệu.
4. Phác grain dự kiến: một dòng fact là sự kiện gì.
5. Cả nhóm thống nhất đề tài trước khi viết DDL.

**Sản phẩm.** Mục 1 của báo cáo (bối cảnh, người dùng quyết định, KPI, nguồn dữ liệu) và danh sách cột nguồn.

**Xong khi.** Người ngoài nhóm đọc một trang vẫn chỉ ra được quyết định cần hỗ trợ và dữ liệu sẽ dùng.

### Giai đoạn 2 — Thiết kế kho dữ liệu và hoàn thiện ETL

**Mục tiêu.** Có mô hình đa chiều và một pipeline đưa được dữ liệu nguồn vào đúng grain.

**Việc cần làm**

1. Chốt star schema hoặc snowflake. Star là mặc định trong `src/database/schema.sql`. Chỉ snowflake hóa nhánh phân cấp nào thực sự cần quản lý riêng.
2. Với mỗi fact, ghi grain, loại fact (transaction, periodic snapshot hoặc accumulating snapshot) và loại measure (additive, semi-additive, non-additive).
3. Gán surrogate key cho dimension. Giữ business key để truy vết nguồn.
4. Chọn SCD. Thuộc tính hay đổi và cần xem theo lịch sử thì dùng Type 2 (cột `effective_from`, `effective_to`, `is_current` đã có trong khung).
5. Sửa `extract`, `transform`, `load` trong `src/etl/pipeline.py`.
6. Đối soát: số dòng nguồn, số dòng bị loại, tổng measure trước và sau khi nạp.

Chạy thử khung hiện tại:

```bash
python src/etl/pipeline.py
```

Khi chưa có file nguồn, pipeline dùng vài dòng demo và ghi `data/processed/fact_event.csv`. Đặt CSV thật tại `data/raw/source.csv` (cột `txn_id`, `txn_date`, `entity_id`, `entity_name`, `amount`, `quantity`) để đi theo nhánh đọc file. Đổi tên cột cho khớp đề tài, đừng giữ mãi dữ liệu demo.

**Sản phẩm.** `schema.sql` chạy được, sơ đồ sao/bông tuyết trong báo cáo, pipeline nạp được dữ liệu mẫu, bảng đối soát số liệu.

**Xong khi.** Truy vấn `SUM` trên fact khớp số đã kiểm trên nguồn, trong sai số mà nhóm giải thích được (dòng bẩn bị loại, quy đổi đơn vị, lọc khoảng thời gian).

### Giai đoạn 3 — Backend và frontend

**Mục tiêu.** Kho nằm trên một CSDL thật, truy vấn được theo kiểu OLAP, và có giao diện để lọc, xem chỉ số.

**Việc cần làm**

1. Tạo CSDL và chạy `src/database/schema.sql`. Khung viết cho PostgreSQL. Nếu dùng SQL Server hoặc MySQL, đổi kiểu khóa tăng tự động và kiểu boolean theo ghi chú đầu file.
2. Nối `load()` của ETL vào `dw.dim_date`, `dw.dim_entity`, `dw.fact_event` bằng một transaction. Không ghi đè fact khi chạy lại mà chưa có khóa chống trùng.
3. Viết ít nhất bốn truy vấn: slice, dice, roll-up, drill-down. Mẫu nằm cuối `schema.sql`.
4. Dựng dashboard từ `src/frontend/app.py`.

```bash
pip install streamlit pandas
streamlit run src/frontend/app.py
```

Màn hình mặc định đọc dữ liệu demo và có bộ lọc năm, phân khúc, thẻ chỉ số, biểu đồ theo quý. Việc của nhóm là thay `load_facts()` bằng truy vấn OLAP và đọc chuỗi kết nối từ biến môi trường, không ghi mật khẩu vào Git.

5. Mỗi KPI ở giai đoạn 1 phải xuất hiện trên dashboard hoặc trong một truy vấn được dẫn từ giao diện.

**Sản phẩm.** CSDL có dữ liệu, script OLAP, dashboard chạy được, ảnh chụp màn hình trong báo cáo.

**Xong khi.** Đổi bộ lọc trên giao diện làm các chỉ số đổi đúng với kết quả chạy SQL tay.

### Giai đoạn 4 — Hệ hỗ trợ quyết định

**Mục tiêu.** Một DSS đơn giản, đọc số đo từ kho và trả về một khuyến nghị kèm lý do.

Khung `src/dss/model.py` đi theo ba bước:

- **Intelligence:** loại phương án thiếu dữ liệu tiêu chí.
- **Design:** chuẩn hóa min-max, chấm điểm có trọng số (`higher_is_better=False` với chi phí hoặc rủi ro).
- **Choice:** chọn phương án điểm cao nhất nếu vượt ngưỡng; không vượt thì trả `CHUA_QUYET`.

```bash
python src/dss/model.py
```

Lệnh này in khuyến nghị trên ba nhóm hàng mẫu. Nhóm phải thay bằng bài toán của mình.

**Việc cần làm**

1. Gắn DSS với đúng quyết định đã viết ở giai đoạn 1.
2. Lấy đầu vào bằng truy vấn aggregate trên kho (một view hoặc một hàm đọc SQL). Không đọc `data/raw/`.
3. Công bố tiêu chí, trọng số, ngưỡng và cách chuẩn hóa trong báo cáo. Trọng số phải có lý do nghiệp vụ.
4. Thêm một kịch bản what-if: đổi một trọng số hoặc một ngưỡng rồi chỉ ra khuyến nghị đổi hay giữ nguyên.
5. In ra thứ hạng và câu giải thích, như `Recommendation.reason`.

**Sản phẩm.** Module DSS chạy trên số liệu của kho, một bảng tiêu chí, một ví dụ what-if trong báo cáo và trên slide.

**Xong khi.** Che tên phương án, người đọc vẫn hiểu vì sao hệ thống chọn phương án đó từ các con số trong kho.

### Giai đoạn 5 — Đánh giá, hạn chế, hướng phát triển

**Mục tiêu.** Nói rõ hệ thống làm được gì, chỗ nào còn yếu, và bước tiếp theo có căn cứ.

**Việc cần làm**

1. Đối chiếu từng KPI giai đoạn 1 với màn hình hoặc truy vấn thực tế. KPI chưa làm được thì ghi là hạn chế, không bỏ khỏi danh sách.
2. Đo chất lượng ETL: số dòng loại, các quy tắc làm sạch, độ lệch tổng measure so với nguồn.
3. Với DSS, kiểm tra trên một tập tình huống nhỏ: khuyến nghị có khớp phán đoán nghiệp vụ đã thống nhất hay không, và lệch ở đâu.
4. Nêu hạn chế thật của đồ án (dữ liệu thiếu lịch sử, SCD chưa phủ hết thuộc tính, dashboard chưa phân quyền, mô hình chỉ là điểm có trọng số, chưa có thí nghiệm thống kê).
5. Đề xuất hướng phát triển gắn hạn chế đó: snapshot tồn kho, phân quyền người dùng, kiểm định trọng số, bổ sung nguồn.

**Sản phẩm.** Mục đánh giá của báo cáo, có bảng đối chiếu KPI và mục hạn chế không chung chung.

**Xong khi.** Mỗi hạn chế đi kèm một hướng xử lý mà nhóm khác có thể thực hiện tiếp.

### Giai đoạn 6 — Báo cáo, dữ liệu, ZIP và nộp bài

**Mục tiêu.** Gói nộp đủ thành phần, đúng hạn, trên LMS.

**Hạn chót: 23:59, Chủ nhật 15/11/2026.** Nộp qua e-learning của môn. Không chờ buổi thuyết trình mới nộp báo cáo.

**Việc cần làm**

1. Hoàn thiện báo cáo PDF: bài toán, thiết kế, ETL, OLAP, giao diện, DSS, đánh giá, phân công, tài liệu tham khảo.
2. Trang bìa có tên môn, mã CO4031, học kỳ 261, tên nhóm, họ tên và MSSV. Nhóm video thì có link trên trang bìa.
3. Xuất slide PDF vào `docs/`.
4. Rà `src/` và `data/` để giảng viên chạy lại được các lệnh trong mục 4. Xóa mật khẩu, file cache, môi trường ảo.
5. Nếu mã nguồn nằm trên GitHub, kiểm tra quyền truy cập và ghi URL trong báo cáo.
6. Nén đúng cây thư mục (báo cáo, slide, `src/`, `data/`) thành một file ZIP và nộp trước 23:59 ngày 15/11/2026.
7. Đăng ký hình thức thuyết trình với giảng viên.

Gợi ý bố cục báo cáo:

1. Giới thiệu và bài toán
2. Thiết kế kho dữ liệu
3. ETL và chất lượng dữ liệu
4. OLAP và dashboard
5. Mô hình DSS
6. Đánh giá, hạn chế, hướng phát triển
7. Phân công và tài liệu tham khảo

## 5. Thuyết trình

Dự kiến 21–30 nhóm. Mỗi buổi có 4–5 nhóm trình bày trực tiếp. Các nhóm còn lại nộp video.

| Buổi | Tuần | Ngày | Hình thức |
| --- | --- | --- | --- |
| 1 | 13 | 19/11/2026 | Trực tiếp |
| 2 | 14 | 26/11/2026 | Trực tiếp |
| 3 | 15 | 03/12/2026 | Trực tiếp |

**Trực tiếp:** 15 phút trình bày + 5 phút hỏi đáp. Chia phần để mọi thành viên nói.

**Video:** 10–15 phút. Mọi thành viên xuất hiện và trình bày. Hình và tiếng phải rõ. Đăng YouTube unlisted hoặc Google Drive (mở quyền xem) và dán link lên trang bìa.

Nội dung nên đi cùng bài toán chứ không đọc slide liệt kê công nghệ: bài toán, sơ đồ kho, một luồng ETL, một truy vấn OLAP trên dashboard, một khuyến nghị DSS và hạn chế chính.

## 6. Checklist trước khi nén ZIP

- [ ] Đề tài có quyết định cụ thể và kho dữ liệu là nơi chứa dữ liệu cho quyết định đó
- [ ] `schema.sql` tạo được fact, dimension, khóa và chỉ mục
- [ ] ETL chạy lại được trên dữ liệu mẫu và có số liệu đối soát
- [ ] Có slice, dice, roll-up, drill-down
- [ ] Dashboard lọc được và số khớp SQL
- [ ] DSS đọc từ kho, có trọng số, ngưỡng và câu giải thích
- [ ] Báo cáo có đánh giá, hạn chế, hướng phát triển và bảng phân công
- [ ] Slide PDF nằm trong `docs/`
- [ ] Link video trên trang bìa nếu không trình bày trực tiếp
- [ ] Mọi thành viên có phần trình bày
- [ ] ZIP nộp LMS trước 23:59 ngày 15/11/2026

## 7. Tài liệu nên dùng khi viết báo cáo

1. W. H. Inmon, *Building the Data Warehouse*, 4th ed., Wiley, 2005.
2. R. Kimball, M. Ross, *The Data Warehouse Toolkit*, 3rd ed., Wiley, 2013. Dùng cho grain, fact, dimension, SCD.
3. E. Turban, J. E. Aronson, T.-P. Liang, *Decision Support Systems and Intelligent Systems*, 7th ed., Prentice-Hall, 2005.
4. R. Elmasri, S. B. Navathe, *Fundamentals of Database Systems*, 7th ed., Addison-Wesley, 2016.
5. R. Sharda, D. Delen, E. Turban, *Analytics, Data Science, & Artificial Intelligence: Systems for Decision Support*, 7th ed., Pearson, 2020.
6. J. Han, M. Kamber, J. Pei, *Data Mining: Concepts and Techniques*, 3rd ed., Morgan Kaufmann, 2012.
7. F. Burstein, C. W. Holsapple (eds.), *Handbook on Decision Support Systems*, Springer, 2008.
8. Trần Minh Quang và cộng sự, *Cơ sở dữ liệu: khái niệm, phương pháp, và kỹ thuật phân tích thiết kế*, NXB ĐHQG-HCM, 2025.

Khi giải thích ba giai đoạn Intelligence, Design và Choice trong DSS, dẫn mô hình ra quyết định của Herbert Simon cùng các giáo trình DSS ở mục 3 và 5.
