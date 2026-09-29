# Kho dữ liệu và Hệ hỗ trợ Quyết định trên dữ liệu chứng khoán NIFTY-50

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

1. Chọn ngành để tăng tỷ trọng trong quý tới (nhà đầu tư cá nhân).
2. Sàng lọc cổ phiếu cho danh mục dài hạn (quản lý quỹ).
3. Chọn ngành, mã phòng thủ khi thị trường khủng hoảng (so sánh giai đoạn 2008 và 2020).
4. Chọn thời điểm đặt lệnh lớn để ít ảnh hưởng giá (quỹ đầu tư).
5. Xếp hạng ký quỹ theo quý (bộ phận quản trị rủi ro của công ty chứng khoán).

KPI dự kiến: lợi nhuận, độ biến động, giá trị giao dịch và tỷ lệ giao nhận thực theo ngành và theo thời gian.

## Dữ liệu

- **Nguồn:** [NIFTY-50 Stock Market Data (2000 - 2021)](https://www.kaggle.com/datasets/rohanrao/nifty50-stock-market-data) trên Kaggle, Version 15, dữ liệu gốc từ NSE India.
- **Giấy phép:** _(kiểm tra mục License trên Kaggle và điền)_.
- **Phạm vi:** 50 cổ phiếu thuộc chỉ số NIFTY-50, giao dịch hằng ngày từ 03/01/2000 đến 30/04/2021, tổng cộng 235.192 dòng.

Các file trong `data/raw/`:

| File | Nội dung |
| --- | --- |
| `<MÃ>.csv` (50 file) | Giá và khối lượng giao dịch theo ngày của từng mã |
| `NIFTY50_all.csv` | Gộp của 50 file trên, trùng hoàn toàn. ETL không đọc file này |
| `stock_metadata.csv` | Tên công ty, ngành, mã hiện hành, mã ISIN |

Các cột của file giá: `Date, Symbol, Series, Prev Close, Open, High, Low, Last, Close, VWAP, Volume, Turnover, Trades, Deliverable Volume, %Deliverble`.

### Đặc điểm dữ liệu cần xử lý trong ETL

- **`Turnover` bị phóng to 100.000 lần:** `Turnover / (VWAP × Volume)` luôn xấp xỉ 100.000. Giá trị giao dịch thực tính bằng rupee là `Turnover / 100000`.
- **Giá chưa điều chỉnh** cho chia tách và thưởng cổ phiếu: có 163 phiên biến động quá 20%. Trong đó có các ngày chia tách (giảm khoảng 50%, 80%, 90%), các ngày niêm yết (`Prev Close` là mệnh giá) và các biến động thật (phiên tăng trần, COVID tháng 3/2020).
- **Đổi mã chứng khoán:** 16 trên 50 công ty từng đổi mã (ví dụ `INFOSYSTCH` sang `INFY`, `UTIBANK` sang `AXISBANK`). Business key là tên file hoặc mã ISIN, còn mã chứng khoán được theo dõi bằng SCD Type 2.
- **Không khớp tên:** metadata ghi mã `M&M` nhưng tên file là `MM.csv`.
- **Dữ liệu thiếu có quy luật:** `Trades` chỉ có từ 01/06/2011; `Deliverable Volume` và `%Deliverble` chỉ có từ năm 2002. Lưu là NULL, không thay bằng 0.
- **Phân bố ngành lệch:** 13 ngành, trong đó 5 ngành chỉ có 1 mã.
- Cột `Series` luôn là `EQ`, không có ngày trùng và không có giá âm.

## Cấu trúc thư mục

```text
.
├── GUIDE.md               # lộ trình và yêu cầu bài tập lớn
├── README.md
├── data/
│   ├── raw/               # dữ liệu nguồn NIFTY-50
│   └── processed/         # đầu ra trung gian của ETL (không sửa tay)
├── docs/                  # báo cáo PDF và slide PDF
└── src/
    ├── database/schema.sql    # DDL kho dữ liệu và truy vấn OLAP
    ├── etl/pipeline.py        # Extract, Transform, Load
    ├── frontend/app.py        # dashboard Streamlit
    └── dss/model.py           # mô hình hỗ trợ quyết định
```

## Cài đặt và chạy

Yêu cầu: Python 3.11 trở lên và PostgreSQL.

```bash
pip install pandas streamlit "psycopg[binary]"
```

Thứ tự chạy:

```bash
# 1. Tạo schema kho dữ liệu
psql -d <ten_csdl> -f src/database/schema.sql

# 2. Chạy ETL
python src/etl/pipeline.py

# 3. Mở dashboard
streamlit run src/frontend/app.py

# 4. Chạy mô hình DSS
python src/dss/model.py
```

Chuỗi kết nối CSDL đọc từ biến môi trường hoặc file `.env` (đã có trong `.gitignore`). Không ghi mật khẩu vào mã nguồn.

## Trạng thái

Các file trong `src/` hiện vẫn là khung mẫu của môn học và chạy trên dữ liệu demo, chưa đọc dữ liệu NIFTY-50.

| Giai đoạn | Nội dung | Hạn | Trạng thái |
| --- | --- | --- | --- |
| 1 | Chốt bài toán, KPI, nguồn dữ liệu | 04/10 | Đã chọn và khảo sát dữ liệu, chưa chốt bài toán |
| 2 | Schema và ETL | 25/10 | Chưa bắt đầu |
| 3 | CSDL, OLAP, dashboard | 01/11 | Chưa bắt đầu |
| 4 | DSS trên số liệu của kho | 08/11 | Chưa bắt đầu |
| 5 | Đánh giá, hạn chế, hướng phát triển | 12/11 | Chưa bắt đầu |
| 6 | Báo cáo, slide, ZIP, nộp LMS | 15/11 | Chưa bắt đầu |
