"""
CO4031 | Khung dashboard truy vấn kho dữ liệu.

Cài và chạy:
    pip install streamlit pandas
    streamlit run src/frontend/app.py

Việc nhóm phải thay:
    - get_connection(): kết nối đúng CSDL đang chứa schema dw.
    - load_facts(): SELECT từ dw.fact_event JOIN các dimension.
    - Bộ lọc sidebar và biểu đồ theo KPI đã chốt ở giai đoạn phân tích.
"""

from __future__ import annotations

from decimal import Decimal

import pandas as pd
import streamlit as st

# Dữ liệu minh họa, cùng hạt với data/processed/fact_event.csv do ETL tạo ra.
DEMO_FACTS = pd.DataFrame(
    [
        {"year": 2026, "quarter": 1, "segment": "A", "amount": 200.50, "quantity": 3},
        {"year": 2026, "quarter": 1, "segment": "B", "amount": 90.00, "quantity": 1},
        {"year": 2026, "quarter": 2, "segment": "A", "amount": 150.00, "quantity": 4},
        {"year": 2025, "quarter": 4, "segment": "B", "amount": 70.00, "quantity": 2},
    ]
)


def get_connection():
    """TODO: trả về kết nối CSDL. Đọc chuỗi kết nối từ biến môi trường, không hard-code mật khẩu."""
    return None


@st.cache_data(show_spinner=False)
def load_facts() -> pd.DataFrame:
    """
    TODO: thay DEMO_FACTS bằng kết quả OLAP, ví dụ:

        SELECT d.year, d.quarter, e.segment,
               SUM(f.amount) AS amount,
               SUM(f.quantity) AS quantity
        FROM dw.fact_event f
        JOIN dw.dim_date d ON d.date_key = f.date_key
        JOIN dw.dim_entity e ON e.entity_key = f.entity_key
        GROUP BY d.year, d.quarter, e.segment
    """
    if get_connection() is None:
        return DEMO_FACTS.copy()
    raise NotImplementedError("Viết truy vấn OLAP tại đây sau khi đã có kết nối.")


def main() -> None:
    st.set_page_config(page_title="CO4031 Dashboard", layout="wide")
    st.title("Dashboard kho dữ liệu")
    st.caption("Khung giao diện. Đang hiển thị dữ liệu demo cho đến khi nối được CSDL.")

    facts = load_facts()
    years = sorted(facts["year"].unique())
    segments = sorted(facts["segment"].unique())

    with st.sidebar:
        st.header("Bộ lọc")
        selected_years = st.multiselect("Năm", years, default=years)
        selected_segments = st.multiselect("Phân khúc", segments, default=segments)

    view = facts[
        facts["year"].isin(selected_years) & facts["segment"].isin(selected_segments)
    ]
    if view.empty:
        st.warning("Không có dòng nào khớp bộ lọc.")
        return

    total_amount = Decimal(str(view["amount"].sum()))
    total_quantity = Decimal(str(view["quantity"].sum()))
    col_amount, col_quantity, col_rows = st.columns(3)
    col_amount.metric("Tổng giá trị", f"{total_amount:,.2f}")
    col_quantity.metric("Tổng số lượng", f"{total_quantity:,.0f}")
    col_rows.metric("Số nhóm", f"{len(view)}")

    by_period = (
        view.groupby(["year", "quarter"], as_index=False)["amount"]
        .sum()
        .sort_values(["year", "quarter"])
    )
    by_period["period"] = by_period["year"].astype(str) + "-Q" + by_period["quarter"].astype(str)
    st.subheader("Giá trị theo quý")
    st.bar_chart(by_period.set_index("period")["amount"])

    st.subheader("Chi tiết đã lọc")
    st.dataframe(view, use_container_width=True)


if __name__ == "__main__":
    main()
