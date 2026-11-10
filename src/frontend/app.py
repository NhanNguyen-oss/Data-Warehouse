"""London road safety dashboard: streamlit run src/frontend/app.py."""
from __future__ import annotations
import pandas as pd
import psycopg
import streamlit as st
from warehouse import DatabaseConfigurationError, load_monthly_facts
from dss_panel import column_labels, render_dss

PAGES = {"BI Dashboard": "Bảng điều khiển BI", "Decision Support": "Hỗ trợ ra quyết định"}

@st.cache_data(ttl=60, show_spinner=False)
def load_facts():
    return pd.DataFrame(load_monthly_facts())

def main():
    st.set_page_config(page_title="An toàn giao thông London", layout="wide")
    with st.sidebar:
        page = st.radio("Không gian làm việc", list(PAGES), format_func=PAGES.get, key="workspace")
    st.title("London · " + PAGES[page])
    st.caption("Kho dữ liệu PostgreSQL · STATS19 · 2021–2025 · London")
    with st.sidebar:
        st.header("Bộ lọc")
        if st.button("Làm mới dữ liệu"):
            load_facts.clear()
    try:
        with st.spinner("Đang truy vấn kho dữ liệu…"):
            facts = load_facts()
    except (DatabaseConfigurationError, psycopg.Error):
        st.error("Không đọc được kho dữ liệu. Kiểm tra DW_DATABASE_URL trong file .env của dự án, "
                 "Docker Desktop và schema dw. Dashboard không hiển thị dữ liệu demo.")
        st.stop()
    if facts.empty:
        st.warning("Không có dữ liệu London giai đoạn 2021–2025. Kiểm tra lần nạp STATS19.")
        st.stop()
    with st.sidebar:
        years = sorted(facts.year.unique().tolist())
        selected_years = st.multiselect("Năm", years, default=years)
        labels = facts.set_index("authority_code").authority_name.to_dict()
        authorities = sorted(labels)
        selected_authorities = st.multiselect("Địa bàn", authorities, default=authorities,
            format_func=lambda code: f"{labels[code]} ({code})")
    view = facts[facts.year.isin(selected_years) & facts.authority_code.isin(selected_authorities)]
    if view.empty:
        st.info("Chọn ít nhất một năm và một địa bàn có dữ liệu.")
        st.stop()
    st.caption("Phạm vi đang chọn: " + ", ".join(map(str, sorted(selected_years)))
               + f" · {len(selected_authorities)} địa bàn · Heathrow được gộp vào Hillingdon")
    if page == "Decision Support":
        render_dss(view, selected_years)
    else:
        render_bi(view)


def render_bi(view):
    st.caption("Khám phá số liệu lịch sử về va chạm và nạn nhân trong phạm vi đang chọn.")
    missing = int(view.adjustment_missing.sum())
    cols = st.columns(4)
    for col, label, value in zip(cols[:3], ["Số vụ va chạm", "Số nạn nhân", "Số tử vong"],
            [view.collisions.sum(), view.casualties.sum(), view.fatalities.sum()]):
        col.metric(label, f"{value:,.0f}")
    cols[3].metric("KSI hiệu chỉnh (người)", "Chưa đầy đủ" if missing else f"{view.ksi_adjusted.sum():,.1f}")
    if missing:
        st.warning(f"{missing:,} nạn nhân thiếu số hiệu chỉnh mức độ nghiêm trọng; "
                   "không thể tính tổng KSI hiệu chỉnh.")
    monthly = view.groupby(["year", "month_number"], as_index=False).collisions.sum()
    monthly["Tháng"] = pd.to_datetime(dict(year=monthly.year, month=monthly.month_number, day=1))
    st.subheader("Số vụ va chạm theo tháng")
    st.line_chart(monthly.set_index("Tháng").collisions.rename("Số vụ va chạm"))
    st.subheader("Số vụ va chạm theo địa bàn")
    by_authority = view.groupby("authority_name").collisions.sum().sort_values(ascending=False)
    st.bar_chart(by_authority.rename("Số vụ va chạm").rename_axis("Địa bàn"))
    detail = view.copy()
    detail.loc[detail.adjustment_missing > 0, "ksi_adjusted"] = float("nan")
    st.subheader("Chi tiết theo địa bàn và tháng")
    st.dataframe(detail, width="stretch", hide_index=True, column_config=column_labels(detail))
    st.download_button("Tải CSV đã lọc", detail.to_csv(index=False).encode("utf-8-sig"),
                       "london_road_safety.csv", "text/csv")
    st.caption("Heathrow được gộp vào Hillingdon. Fact va chạm và fact nạn nhân được tổng hợp "
               "riêng trước khi kết hợp. Dữ liệu Traffic chưa được tích hợp.")

if __name__ == "__main__":
    main()
