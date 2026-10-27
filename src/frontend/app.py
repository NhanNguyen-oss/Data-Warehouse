"""London road safety dashboard: streamlit run src/frontend/app.py."""
from __future__ import annotations
import pandas as pd
import psycopg
import streamlit as st
from warehouse import DatabaseConfigurationError, load_monthly_facts
from dss_panel import render_dss

@st.cache_data(ttl=60, show_spinner=False)
def load_facts():
    return pd.DataFrame(load_monthly_facts())

def main():
    st.set_page_config(page_title="London Road Safety", layout="wide")
    with st.sidebar:
        page = st.radio("Workspace", ["BI Dashboard", "Decision Support"], key="workspace")
    st.title("London · " + page)
    st.caption("PostgreSQL warehouse · STATS19 · 2021–2025 · London")
    with st.sidebar:
        st.header("Filters")
        if st.button("Refresh data"):
            load_facts.clear()
    try:
        with st.spinner("Querying warehouse…"):
            facts = load_facts()
    except (DatabaseConfigurationError, psycopg.Error):
        st.error("Cannot read the warehouse. Check DW_DATABASE_URL in the project .env, "
                 "Docker Desktop, and the dw schema. No demo data is shown.")
        st.stop()
    if facts.empty:
        st.warning("No London data for 2021–2025. Check the STATS19 load.")
        st.stop()
    with st.sidebar:
        years = sorted(facts.year.unique().tolist())
        selected_years = st.multiselect("Years", years, default=years)
        labels = facts.set_index("authority_code").authority_name.to_dict()
        authorities = sorted(labels)
        selected_authorities = st.multiselect("Authorities", authorities, default=authorities,
            format_func=lambda code: f"{labels[code]} ({code})")
    view = facts[facts.year.isin(selected_years) & facts.authority_code.isin(selected_authorities)]
    if view.empty:
        st.info("Select at least one year and authority with data.")
        st.stop()
    st.caption("Selected scope: " + ", ".join(map(str, sorted(selected_years)))
               + f" · {len(selected_authorities)} authorities · Heathrow included in Hillingdon")
    if page == "Decision Support":
        render_dss(view, selected_years)
    else:
        render_bi(view)


def render_bi(view):
    st.caption("Explore historical collisions and casualties for the selected scope.")
    missing = int(view.adjustment_missing.sum())
    cols = st.columns(4)
    for col, label, value in zip(cols[:3], ["Collisions", "Casualties", "Fatalities"],
            [view.collisions.sum(), view.casualties.sum(), view.fatalities.sum()]):
        col.metric(label, f"{value:,.0f}")
    cols[3].metric("Adjusted KSI (people)", "Incomplete" if missing else f"{view.ksi_adjusted.sum():,.1f}")
    if missing:
        st.warning(f"{missing:,} casualties lack severity adjustments; adjusted KSI total is unavailable.")
    monthly = view.groupby(["year", "month_number"], as_index=False).collisions.sum()
    monthly["period"] = pd.to_datetime(dict(year=monthly.year, month=monthly.month_number, day=1))
    st.subheader("Monthly collisions")
    st.line_chart(monthly.set_index("period").collisions)
    st.subheader("Collisions by authority")
    st.bar_chart(view.groupby("authority_name").collisions.sum().sort_values(ascending=False))
    detail = view.copy()
    detail.loc[detail.adjustment_missing > 0, "ksi_adjusted"] = float("nan")
    st.subheader("Authority and month detail")
    st.dataframe(detail, width="stretch", hide_index=True)
    st.download_button("Download filtered CSV", detail.to_csv(index=False).encode("utf-8-sig"),
                       "london_road_safety.csv", "text/csv")
    st.caption("Heathrow is included in Hillingdon. Collision and casualty facts are aggregated "
               "separately before joining. Traffic integration is pending.")

if __name__ == "__main__":
    main()
