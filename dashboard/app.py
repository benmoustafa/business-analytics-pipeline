"""
dashboard/app.py

Streamlit KPI dashboard for the Olist Business Analytics pipeline.

Modes:
  - Docker/Postgres: reads from dbt marts in PostgreSQL
  - Local: reads Parquet files from data/processed/ and computes metrics in-memory

Usage:
    streamlit run dashboard/app.py
"""

import os
import zipfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Olist Business Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Data loading — Parquet (local) or Postgres (Docker)
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def ensure_data_available():
    """Ensure Parquet files exist in DATA_DIR. Unpacks processed.zip if missing."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    existing_parquet = list(DATA_DIR.glob("*.parquet"))
    if len(existing_parquet) >= 9:
        return

    # Check zip location
    zip_root = Path(__file__).resolve().parent.parent / "data" / "processed.zip"
    zip_dir = DATA_DIR.parent / "processed.zip"
    target_zip = zip_root if zip_root.exists() else (zip_dir if zip_dir.exists() else None)

    if target_zip:
        with zipfile.ZipFile(target_zip, "r") as zf:
            zf.extractall(DATA_DIR)
        return

    # Download processed.zip from raw GitHub as fallback
    github_raw_url = "https://raw.githubusercontent.com/benmoustafa/business-analytics-pipeline/main/data/processed.zip"
    try:
        import urllib.request
        dl_path = DATA_DIR.parent / "processed.zip"
        urllib.request.urlretrieve(github_raw_url, dl_path)
        with zipfile.ZipFile(dl_path, "r") as zf:
            zf.extractall(DATA_DIR)
    except Exception as err:
        st.error(f"Could not auto-download data: {err}")


@st.cache_data(ttl=600)
def load_data():
    """Load all datasets from local Parquet files and build the mart-equivalent DataFrames."""
    ensure_data_available()
    orders = pd.read_parquet(DATA_DIR / "olist_orders_dataset.parquet")
    items = pd.read_parquet(DATA_DIR / "olist_order_items_dataset.parquet")
    customers = pd.read_parquet(DATA_DIR / "olist_customers_dataset.parquet")
    payments = pd.read_parquet(DATA_DIR / "olist_order_payments_dataset.parquet")
    reviews = pd.read_parquet(DATA_DIR / "olist_order_reviews_dataset.parquet")
    products = pd.read_parquet(DATA_DIR / "olist_products_dataset.parquet")
    sellers = pd.read_parquet(DATA_DIR / "olist_sellers_dataset.parquet")
    translations = pd.read_parquet(DATA_DIR / "product_category_name_translation.parquet")

    # Cast timestamps
    for col in [
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]:
        orders[col] = pd.to_datetime(orders[col], errors="coerce")

    # --- Build fact_orders equivalent ---
    items_agg = (
        items.groupby("order_id")
        .agg(
            item_count=("order_item_id", "count"),
            revenue=("price", "sum"),
            freight_total=("freight_value", "sum"),
        )
        .assign(gmv=lambda d: d["revenue"] + d["freight_total"])
        .reset_index()
    )

    payments_agg = (
        payments.groupby("order_id")
        .agg(total_payment_value=("payment_value", "sum"))
        .reset_index()
    )

    reviews_dedup = (
        reviews.sort_values("review_answer_timestamp", ascending=False)
        .drop_duplicates(subset=["order_id"], keep="first")
        [["order_id", "review_score"]]
    )

    # Merge into fact table
    fact = orders.merge(customers[["customer_id", "customer_unique_id", "customer_city", "customer_state"]], on="customer_id", how="left")
    fact = fact.merge(items_agg, on="order_id", how="left")
    fact = fact.merge(payments_agg, on="order_id", how="left")
    fact = fact.merge(reviews_dedup, on="order_id", how="left")

    # Delivery metrics
    fact["order_to_delivery_days"] = (
        (fact["order_delivered_customer_date"] - fact["order_purchase_timestamp"])
        .dt.total_seconds() / 86400
    )
    fact["delivered_on_time"] = (
        fact["order_delivered_customer_date"] <= fact["order_estimated_delivery_date"]
    )
    fact["purchase_date"] = fact["order_purchase_timestamp"].dt.date
    fact["purchase_month"] = fact["order_purchase_timestamp"].dt.to_period("M").astype(str)

    # Products with English category
    products_en = products.merge(translations, on="product_category_name", how="left")
    products_en["category_en"] = products_en["product_category_name_english"].fillna("unknown")

    # Items with category
    items_cat = items.merge(products_en[["product_id", "category_en"]], on="product_id", how="left")

    return fact, items_cat, customers, sellers


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
try:
    fact, items_cat, customers, sellers = load_data()
except Exception as e:
    st.error(f"⚠️ Could not load data: {e}")
    st.info("Make sure you've run `python ingestion/extract.py` and `python ingestion/load.py` first.")
    st.stop()


# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.markdown("## 🔍 Filters")

# Date range
min_date = fact["order_purchase_timestamp"].min().date()
max_date = fact["order_purchase_timestamp"].max().date()
date_range = st.sidebar.date_input(
    "Order date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

# State filter
all_states = sorted(fact["customer_state"].dropna().unique())
selected_states = st.sidebar.multiselect("Customer state", all_states, default=[])

# Status filter
all_statuses = sorted(fact["order_status"].unique())
selected_statuses = st.sidebar.multiselect("Order status", all_statuses, default=["delivered"])

# Apply filters
mask = pd.Series(True, index=fact.index)

if len(date_range) == 2:
    mask &= (fact["purchase_date"] >= date_range[0]) & (fact["purchase_date"] <= date_range[1])

if selected_states:
    mask &= fact["customer_state"].isin(selected_states)

if selected_statuses:
    mask &= fact["order_status"].isin(selected_statuses)

df = fact[mask].copy()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div style="text-align: center; padding: 1rem 0 0.5rem 0;">
        <h1 style="font-size: 2.2rem; margin-bottom: 0.2rem;">📊 Olist Business Analytics Dashboard</h1>
        <p style="color: #888; font-size: 1rem;">
            Brazilian E-Commerce · 100k orders · 2016–2018
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.divider()


# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
col1, col2, col3, col4, col5 = st.columns(5)

total_orders = len(df)
total_revenue = df["revenue"].sum()
avg_order_value = df["revenue"].mean() if total_orders else 0
avg_delivery_days = df["order_to_delivery_days"].mean()
avg_review_score = df["review_score"].mean()

col1.metric("🛒 Total Orders", f"{total_orders:,.0f}")
col2.metric("💰 Total Revenue", f"R$ {total_revenue:,.0f}")
col3.metric("📦 Avg Order Value", f"R$ {avg_order_value:,.2f}")
col4.metric("🚚 Avg Delivery (days)", f"{avg_delivery_days:.1f}" if pd.notna(avg_delivery_days) else "N/A")
col5.metric("⭐ Avg Review Score", f"{avg_review_score:.2f}" if pd.notna(avg_review_score) else "N/A")

st.divider()


# ---------------------------------------------------------------------------
# Row 1: Revenue trend + On-time delivery rate
# ---------------------------------------------------------------------------
r1_left, r1_right = st.columns([3, 2])

with r1_left:
    st.subheader("📈 Monthly Revenue Trend")
    monthly = (
        df.groupby("purchase_month")
        .agg(revenue=("revenue", "sum"), orders=("order_id", "count"))
        .reset_index()
    )
    if not monthly.empty:
        fig_rev = px.bar(
            monthly, x="purchase_month", y="revenue",
            labels={"purchase_month": "Month", "revenue": "Revenue (R$)"},
            color_discrete_sequence=["#636EFA"],
        )
        fig_rev.update_layout(
            xaxis_tickangle=-45,
            margin=dict(t=20, b=60),
            height=380,
        )
        st.plotly_chart(fig_rev, use_container_width=True)

with r1_right:
    st.subheader("🚚 On-Time Delivery Rate")
    delivered = df[df["order_delivered_customer_date"].notna()].copy()
    if not delivered.empty:
        on_time_pct = delivered["delivered_on_time"].mean() * 100
        late_pct = 100 - on_time_pct

        fig_ontime = go.Figure(go.Pie(
            values=[on_time_pct, late_pct],
            labels=["On Time", "Late"],
            marker_colors=["#2ecc71", "#e74c3c"],
            hole=0.55,
            textinfo="percent+label",
        ))
        fig_ontime.update_layout(
            margin=dict(t=20, b=20),
            height=380,
            showlegend=False,
            annotations=[dict(text=f"{on_time_pct:.1f}%", x=0.5, y=0.5, font_size=28, showarrow=False)],
        )
        st.plotly_chart(fig_ontime, use_container_width=True)
    else:
        st.info("No delivered orders in the current filter.")


# ---------------------------------------------------------------------------
# Row 2: Top categories + Review distribution
# ---------------------------------------------------------------------------
r2_left, r2_right = st.columns(2)

with r2_left:
    st.subheader("🏷️ Top 10 Product Categories by Revenue")
    # Join items with filtered orders
    filtered_items = items_cat[items_cat["order_id"].isin(df["order_id"])]
    cat_rev = (
        filtered_items.groupby("category_en")
        .agg(revenue=("price", "sum"), qty=("order_item_id", "count"))
        .sort_values("revenue", ascending=True)
        .tail(10)
        .reset_index()
    )
    if not cat_rev.empty:
        fig_cat = px.bar(
            cat_rev, x="revenue", y="category_en", orientation="h",
            labels={"revenue": "Revenue (R$)", "category_en": "Category"},
            color_discrete_sequence=["#FF6B6B"],
        )
        fig_cat.update_layout(margin=dict(t=20, b=20, l=10), height=400, yaxis_title="")
        st.plotly_chart(fig_cat, use_container_width=True)

with r2_right:
    st.subheader("⭐ Review Score Distribution")
    review_dist = df["review_score"].dropna().value_counts().sort_index().reset_index()
    review_dist.columns = ["score", "count"]
    if not review_dist.empty:
        colors = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#27ae60"]
        fig_review = px.bar(
            review_dist, x="score", y="count",
            labels={"score": "Review Score", "count": "Number of Reviews"},
            color="score",
            color_discrete_sequence=colors,
        )
        fig_review.update_layout(
            margin=dict(t=20, b=20),
            height=400,
            showlegend=False,
            xaxis=dict(dtick=1),
        )
        st.plotly_chart(fig_review, use_container_width=True)


# ---------------------------------------------------------------------------
# Row 3: Revenue by state (map) + Payment type breakdown
# ---------------------------------------------------------------------------
r3_left, r3_right = st.columns(2)

with r3_left:
    st.subheader("🗺️ Revenue by State")
    state_rev = (
        df.groupby("customer_state")
        .agg(revenue=("revenue", "sum"), orders=("order_id", "count"))
        .reset_index()
    )
    if not state_rev.empty:
        fig_state = px.bar(
            state_rev.sort_values("revenue", ascending=True).tail(15),
            x="revenue", y="customer_state", orientation="h",
            labels={"revenue": "Revenue (R$)", "customer_state": "State"},
            color="revenue",
            color_continuous_scale="Viridis",
        )
        fig_state.update_layout(margin=dict(t=20, b=20, l=10), height=420, yaxis_title="")
        st.plotly_chart(fig_state, use_container_width=True)

with r3_right:
    st.subheader("💳 Payment Type Breakdown")
    # Get payments for filtered orders
    filtered_order_ids = set(df["order_id"])
    payments_all = pd.read_parquet(DATA_DIR / "olist_order_payments_dataset.parquet")
    filtered_payments = payments_all[payments_all["order_id"].isin(filtered_order_ids)]

    pay_dist = (
        filtered_payments.groupby("payment_type")
        .agg(total=("payment_value", "sum"), count=("payment_type", "count"))
        .sort_values("total", ascending=False)
        .reset_index()
    )
    if not pay_dist.empty:
        fig_pay = go.Figure(go.Pie(
            values=pay_dist["total"],
            labels=pay_dist["payment_type"],
            hole=0.4,
            textinfo="percent+label",
            marker_colors=["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"],
        ))
        fig_pay.update_layout(margin=dict(t=20, b=20), height=420)
        st.plotly_chart(fig_pay, use_container_width=True)


# ---------------------------------------------------------------------------
# Row 4: RFM Customer Segmentation
# ---------------------------------------------------------------------------
st.divider()
st.subheader("👥 Customer Segmentation (RFM Analysis)")
st.caption("Recency · Frequency · Monetary — the classic customer value framework")

# Compute RFM from delivered orders
delivered_orders = df[df["order_status"] == "delivered"].copy()

if not delivered_orders.empty and "customer_unique_id" in delivered_orders.columns:
    reference_date = delivered_orders["order_purchase_timestamp"].max() + pd.Timedelta(days=1)

    rfm = (
        delivered_orders.groupby("customer_unique_id")
        .agg(
            recency=("order_purchase_timestamp", lambda x: (reference_date - x.max()).days),
            frequency=("order_id", "nunique"),
            monetary=("revenue", "sum"),
        )
        .reset_index()
    )

    # Score each metric 1-5 (quintiles)
    for col in ["recency", "frequency", "monetary"]:
        ascending = col == "recency"  # lower recency = better
        rfm[f"{col}_score"] = pd.qcut(
            rfm[col].rank(method="first"),
            q=5, labels=[5, 4, 3, 2, 1] if ascending else [1, 2, 3, 4, 5],
        ).astype(int)

    rfm["rfm_score"] = rfm["recency_score"] + rfm["frequency_score"] + rfm["monetary_score"]

    # Segment labels
    def segment(row):
        if row["rfm_score"] >= 12:
            return "🏆 Champions"
        elif row["rfm_score"] >= 9:
            return "💎 Loyal"
        elif row["rfm_score"] >= 6:
            return "🔄 At Risk"
        else:
            return "💤 Hibernating"

    rfm["segment"] = rfm.apply(segment, axis=1)

    # Display
    rfm_cols = st.columns([1, 2])

    with rfm_cols[0]:
        seg_counts = rfm["segment"].value_counts().reset_index()
        seg_counts.columns = ["Segment", "Customers"]
        st.dataframe(
            seg_counts.style.format({"Customers": "{:,.0f}"}),
            use_container_width=True,
            hide_index=True,
        )
        st.metric("Unique Customers", f"{len(rfm):,}")

    with rfm_cols[1]:
        seg_summary = (
            rfm.groupby("segment")
            .agg(
                customers=("customer_unique_id", "count"),
                avg_recency=("recency", "mean"),
                avg_frequency=("frequency", "mean"),
                avg_monetary=("monetary", "mean"),
            )
            .reset_index()
        )
        fig_seg = px.scatter(
            seg_summary, x="avg_recency", y="avg_monetary",
            size="customers", color="segment",
            labels={
                "avg_recency": "Avg Recency (days since last order)",
                "avg_monetary": "Avg Monetary (R$)",
            },
            size_max=60,
            color_discrete_sequence=["#2ecc71", "#3498db", "#e67e22", "#95a5a6"],
        )
        fig_seg.update_layout(
            margin=dict(t=20, b=20),
            height=350,
        )
        st.plotly_chart(fig_seg, use_container_width=True)
else:
    st.info("Not enough delivered orders to compute RFM segmentation with current filters.")


# ---------------------------------------------------------------------------
# Row 5: Delivery performance detail
# ---------------------------------------------------------------------------
st.divider()
st.subheader("⏱️ Delivery Time Distribution")

delivered = df[df["order_to_delivery_days"].notna() & (df["order_to_delivery_days"] > 0)].copy()

if not delivered.empty:
    d_cols = st.columns([3, 2])

    with d_cols[0]:
        fig_del = px.histogram(
            delivered, x="order_to_delivery_days",
            nbins=50,
            labels={"order_to_delivery_days": "Days from Order to Delivery"},
            color_discrete_sequence=["#636EFA"],
        )
        fig_del.add_vline(
            x=delivered["order_to_delivery_days"].median(),
            line_dash="dash", line_color="red",
            annotation_text=f"Median: {delivered['order_to_delivery_days'].median():.1f} days",
        )
        fig_del.update_layout(
            margin=dict(t=20, b=20),
            height=350,
            showlegend=False,
        )
        st.plotly_chart(fig_del, use_container_width=True)

    with d_cols[1]:
        st.markdown("**Delivery Stats**")
        stats = delivered["order_to_delivery_days"].describe()
        stat_df = pd.DataFrame({
            "Metric": ["Minimum", "25th percentile", "Median", "Mean", "75th percentile", "Maximum"],
            "Days": [
                f"{stats['min']:.1f}",
                f"{stats['25%']:.1f}",
                f"{stats['50%']:.1f}",
                f"{stats['mean']:.1f}",
                f"{stats['75%']:.1f}",
                f"{stats['max']:.1f}",
            ],
        })
        st.dataframe(stat_df, use_container_width=True, hide_index=True)

        # Delivery by state
        st.markdown("**Slowest States (avg delivery days)**")
        state_delivery = (
            delivered.groupby("customer_state")["order_to_delivery_days"]
            .mean()
            .sort_values(ascending=False)
            .head(5)
            .reset_index()
        )
        state_delivery.columns = ["State", "Avg Days"]
        state_delivery["Avg Days"] = state_delivery["Avg Days"].round(1)
        st.dataframe(state_delivery, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "Data source: [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) · "
    "Pipeline: ingestion → dbt → Airflow → Streamlit · "
    f"Showing {len(df):,} of {len(fact):,} orders"
)
