"""
app.py

Streamlit dashboard for the business analytics pipeline.
Connects to the Postgres warehouse populated by dbt marts.
Fill in real KPI queries once dbt marts (fact_orders, dim_customer, etc.) exist.
"""

import os

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

WAREHOUSE_URL = os.environ.get(
    "WAREHOUSE_URL", "postgresql://postgres:postgres@localhost:5432/warehouse"
)

st.set_page_config(page_title="Business Analytics Dashboard", layout="wide")
st.title("Business Analytics Dashboard")

engine = create_engine(WAREHOUSE_URL)


@st.cache_data(ttl=600)
def run_query(sql: str) -> pd.DataFrame:
    return pd.read_sql(sql, engine)


st.sidebar.header("Filters")
st.sidebar.info(
    "Placeholder filters — wire these up to real dimensions "
    "(region, category, date range) once marts are built."
)

try:
    orders_count = run_query("select count(*) as n from stg_orders").iloc[0]["n"]
    st.metric("Total Orders (staging)", f"{orders_count:,}")
except Exception as e:
    st.warning(f"Could not query warehouse yet — run the pipeline first. ({e})")

st.markdown(
    """
    ### Next steps
    - Replace the placeholder query above with real KPI marts (revenue by category,
      delivery time, customer segmentation, demand forecast vs actual)
    - Add sidebar filters wired to `dim_date`, `dim_product`, `dim_customer`
    """
)
