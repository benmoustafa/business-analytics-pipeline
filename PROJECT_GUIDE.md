# 📘 Project Learning Guide — Business Analytics Pipeline

> **Dataset:** Olist Brazilian E-Commerce (Kaggle: `olistbr/brazilian-ecommerce`)
> **Goal:** End-to-end data pipeline — Ingestion → Transformation → Orchestration → BI Dashboard → ML Model → API

---

## Table of Contents

1. [Project Overview & Architecture](#1-project-overview--architecture)
2. [Step 1 — Kaggle Data Extraction](#2-step-1--kaggle-data-extraction)
3. [Step 2 — Schema Validation & Parquet Loading](#3-step-2--schema-validation--parquet-loading)
4. [Step 3 — Repo Scaffolding](#4-step-3--repo-scaffolding)
5. [Step 4 — dbt Staging Layer](#5-step-4--dbt-staging-layer)
6. [Step 5 — dbt Intermediate Layer](#6-step-5--dbt-intermediate-layer)
7. [Step 6 — dbt Marts (Star Schema)](#7-step-6--dbt-marts-star-schema)
8. [Step 7 — Warehouse Loading](#8-step-7--warehouse-loading)
9. [Step 8 — Orchestration (Airflow + Docker)](#9-step-8--orchestration-airflow--docker)
10. [Key Concepts Glossary](#10-key-concepts-glossary)
11. [How to Run Everything](#11-how-to-run-everything)
12. [What Comes Next](#12-what-comes-next)

---

## 1. Project Overview & Architecture

### What we are building

A **production-style data pipeline** on real e-commerce data. Instead of a single Jupyter notebook (which is what most portfolio projects look like), this project separates every concern into its own layer — exactly how it is done in real companies.

```
┌──────────────┐     ┌──────────────┐     ┌───────────────────┐     ┌─────────────┐
│   Kaggle     │────▶│  Ingestion   │────▶│  Transformation   │────▶│  Analysis   │
│  (raw CSVs)  │     │  (Python)    │     │  (dbt + Postgres) │     │ (Streamlit) │
└──────────────┘     └──────────────┘     └───────────────────┘     └─────────────┘
                                                    │
                                                    ▼
                                          ┌───────────────────┐
                                          │    ML Modeling    │
                                          │  Prophet + LSTM   │
                                          └───────────────────┘
                                                    │
                                                    ▼
                                          ┌───────────────────┐
                                          │   FastAPI serve   │
                                          └───────────────────┘

All orchestrated by Airflow (daily DAG), containerized via Docker Compose.
```

### The dataset

| File | Rows | Key fields |
|---|---|---|
| `olist_orders_dataset.csv` | 99,441 | order status, timestamps |
| `olist_order_items_dataset.csv` | 112,650 | product, seller, price, freight |
| `olist_customers_dataset.csv` | 99,441 | location (city, state, zip) |
| `olist_products_dataset.csv` | 32,951 | category, dimensions, weight |
| `olist_order_payments_dataset.csv` | 103,886 | payment type, value |
| `olist_order_reviews_dataset.csv` | 99,224 | review score, comments |
| `olist_sellers_dataset.csv` | 3,095 | location |
| `olist_geolocation_dataset.csv` | 1,000,163 | zip → lat/lng |
| `product_category_name_translation.csv` | 71 | PT → EN category names |

---

## 2. Step 1 — Kaggle Data Extraction

**File:** [`ingestion/extract.py`](file:///c:/Users/user/Desktop/projects/ingestion/extract.py)

### What it does

1. Checks whether Kaggle credentials exist (in `~/.kaggle/kaggle.json` or env vars)
2. If not, **prompts you interactively** for your username + API key and saves them
3. Downloads the dataset zip from Kaggle (~42 MB)
4. Extracts all 9 CSV files into `data/raw/`
5. Verifies that all 9 CSVs are present

### How Kaggle authentication works

Kaggle uses a JSON file stored at `C:\Users\<you>\.kaggle\kaggle.json`:

```json
{
  "username": "moustafabenabdelhadi",
  "key": "KGAT_..."
}
```

- Your **username** is the last part of your Kaggle profile URL
- Your **API key** starts with `KGAT_` — generated in Kaggle Settings → API

### Key functions

```python
def setup_kaggle_credentials() -> None:
    # Prompts for username + key → writes ~/.kaggle/kaggle.json
    # Only runs if credentials don't already exist

def download_dataset() -> None:
    # Uses the official kaggle Python library to download the zip

def extract_zip() -> None:
    # Unzips the archive into data/raw/ and deletes the zip

def verify_files() -> None:
    # Lists the 9 CSVs and warns if any are missing
```

### Run it

```bash
python ingestion/extract.py
```

---

## 3. Step 2 — Schema Validation & Parquet Loading

**Files:**
- [`ingestion/load.py`](file:///c:/Users/user/Desktop/projects/ingestion/load.py)
- [`ingestion/schemas.py`](file:///c:/Users/user/Desktop/projects/ingestion/schemas.py)

### Why Parquet instead of keeping CSVs?

| Format | Size | Query speed | Type safety |
|---|---|---|---|
| CSV | large | slow (full scan) | everything is a string |
| **Parquet** | ~5× smaller | columnar, very fast | types preserved |

### What `schemas.py` contains

A Python dictionary that defines the **expected schema** for every CSV:

```python
DATASET_SCHEMAS = {
    "olist_orders_dataset.csv": {
        "primary_key": ["order_id"],
        "columns": [
            "order_id", "customer_id", "order_status",
            "order_purchase_timestamp", ...
        ],
    },
    ...
}
```

This is the **contract** — if Kaggle ever changes the file structure, the script fails loudly instead of silently producing wrong data.

### What `load.py` does — step by step

```
For each CSV file:
  1. Read CSV with pandas
  2. validate_columns()   → are all expected columns present?
  3. check_data_quality() → any nulls in key fields? duplicate PKs?
  4. Write to data/processed/<name>.parquet
```

### Data quality findings (real issues found in the Olist dataset)

| File | Issue | Count |
|---|---|---|
| `olist_orders_dataset.csv` | Nulls in `order_approved_at` | 160 |
| `olist_orders_dataset.csv` | Nulls in `order_delivered_customer_date` | 2,965 |
| `olist_products_dataset.csv` | Nulls in `product_category_name` | 610 |
| `olist_order_reviews_dataset.csv` | Duplicate `review_id` values | 814 |

> These are handled later in dbt (deduplicate reviews, fill missing categories with 'unknown').

### Run it

```bash
python ingestion/load.py
```

---

## 4. Step 3 — Repo Scaffolding

### Folder structure

```
projects/
├── ingestion/                  ← Python ingestion scripts
│   ├── extract.py
│   ├── load.py
│   └── schemas.py
├── dbt/                        ← SQL transformation layer
│   ├── dbt_project.yml
│   ├── profiles.yml.example
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   └── tests/
├── orchestration/
│   └── dags/
│       └── pipeline_dag.py     ← Airflow DAG
├── dashboard/
│   ├── app.py                  ← Streamlit dashboard
│   └── Dockerfile
├── api/
│   ├── main.py                 ← FastAPI prediction service
│   └── Dockerfile
├── modeling/                   ← Jupyter notebooks (WIP)
├── scripts/
│   └── init-multiple-dbs.sh    ← Postgres DB init
├── data/
│   ├── raw/                    ← Downloaded CSVs (gitignored)
│   └── processed/              ← Parquet files (gitignored)
├── docker-compose.yml
├── requirements.txt
├── .gitignore
└── README.md
```

### Why this structure matters

- Each folder has **one responsibility** — no mixing of concerns
- Data files are gitignored (too large, regenerated by scripts)
- Anyone can clone the repo and run the extract script to get started

### Git setup

```bash
git init
git add .
git commit -m "feat: initial repo scaffolding"
```

The `.gitignore` excludes:
- `data/` — large CSV and Parquet files
- `__pycache__/`, `.pyc` — Python bytecode
- `.venv/` — virtual environments
- `dbt/target/`, `dbt/logs/` — dbt build artifacts

---

## 5. Step 4 — dbt Staging Layer

**Location:** [`dbt/models/staging/`](file:///c:/Users/user/Desktop/projects/dbt/models/staging)

### What is dbt?

**dbt (data build tool)** is the industry standard for SQL-based data transformation. You write `.sql` files that define how to transform data, and dbt:
- Runs them in the correct dependency order
- Creates views or tables in your database
- Runs data quality tests
- Generates documentation automatically

### The 3-layer architecture

```
Staging       →   Intermediate   →   Marts
(raw → clean)     (aggregations)     (business tables)
```

**Staging rule:** One model per source table. Light cleaning only — rename columns, cast types. **No joins, no business logic.**

### All 8 staging models

| Model | Source table | What changes |
|---|---|---|
| [stg_orders.sql](file:///c:/Users/user/Desktop/projects/dbt/models/staging/stg_orders.sql) | `olist_orders_dataset` | Timestamps cast, columns renamed |
| [stg_customers.sql](file:///c:/Users/user/Desktop/projects/dbt/models/staging/stg_customers.sql) | `olist_customers_dataset` | `customer_*` prefix stripped |
| [stg_order_items.sql](file:///c:/Users/user/Desktop/projects/dbt/models/staging/stg_order_items.sql) | `olist_order_items_dataset` | `shipping_limit_date` cast to timestamp |
| [stg_order_payments.sql](file:///c:/Users/user/Desktop/projects/dbt/models/staging/stg_order_payments.sql) | `olist_order_payments_dataset` | No changes needed |
| [stg_order_reviews.sql](file:///c:/Users/user/Desktop/projects/dbt/models/staging/stg_order_reviews.sql) | `olist_order_reviews_dataset` | Both date columns cast to timestamps |
| [stg_products.sql](file:///c:/Users/user/Desktop/projects/dbt/models/staging/stg_products.sql) | `olist_products_dataset` | Fixes the `_lenght` typo → `_length` |
| [stg_sellers.sql](file:///c:/Users/user/Desktop/projects/dbt/models/staging/stg_sellers.sql) | `olist_sellers_dataset` | `seller_*` prefix stripped |
| [stg_category_translation.sql](file:///c:/Users/user/Desktop/projects/dbt/models/staging/stg_category_translation.sql) | `product_category_name_translation` | `category_name_english` alias |

### Example staging model

```sql
-- stg_orders.sql
with source as (
    select * from {{ source('raw', 'olist_orders_dataset') }}
)

select
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp::timestamp as purchase_ts,   -- cast + rename
    order_approved_at::timestamp        as approved_ts,
    ...
from source
```

> `{{ source('raw', 'olist_orders_dataset') }}` — dbt's way of referencing a raw table.
> `{{ ref('stg_orders') }}` — how downstream models reference this model.

### `schema.yml` — dbt tests

```yaml
models:
  - name: stg_orders
    columns:
      - name: order_id
        tests:
          - unique        # no duplicate orders
          - not_null      # every order has an ID
      - name: order_status
        tests:
          - not_null
```

dbt runs `dbt test` and fails loudly if any assertion is violated.

---

## 6. Step 5 — dbt Intermediate Layer

**Location:** [`dbt/models/intermediate/`](file:///c:/Users/user/Desktop/projects/dbt/models/intermediate)

Intermediate models **aggregate and clean** data so the final mart models stay simple. They are materialized as views (computed on the fly, not stored as tables).

### The 3 intermediate models

#### [`int_orders_items_agg.sql`](file:///c:/Users/user/Desktop/projects/dbt/models/intermediate/int_orders_items_agg.sql)

Rolls up all line items per order into a single summary row:

```sql
select
    order_id,
    count(*)                       as item_count,
    count(distinct product_id)     as distinct_product_count,
    sum(price)                     as revenue,
    sum(freight_value)             as freight_total,
    sum(price + freight_value)     as gmv   -- Gross Merchandise Value
from stg_order_items
group by order_id
```

> **GMV** = Gross Merchandise Value = total money exchanged. A key e-commerce KPI.

#### [`int_orders_payments_agg.sql`](file:///c:/Users/user/Desktop/projects/dbt/models/intermediate/int_orders_payments_agg.sql)

Handles the tricky case where one order has **multiple payment rows** (e.g. part voucher + part credit card):

```sql
select
    order_id,
    sum(payment_value)    as total_payment_value,
    max(case when payment_type = 'credit_card' then 1 else 0 end) as has_credit_card,
    max(case when payment_type = 'boleto'      then 1 else 0 end) as has_boleto,
    -- Dominant payment type (highest value payment wins)
    (array_agg(payment_type order by payment_value desc))[1]      as primary_payment_type
from stg_order_payments
group by order_id
```

#### [`int_orders_reviews_dedup.sql`](file:///c:/Users/user/Desktop/projects/dbt/models/intermediate/int_orders_reviews_dedup.sql)

Fixes the **814 duplicate `review_id`** values from the source:

```sql
select distinct on (order_id)
    order_id, review_id, review_score, ...
from stg_order_reviews
order by order_id, review_answered_ts desc  -- keep most recent answer
```

> `DISTINCT ON` is a PostgreSQL feature that keeps the first row per group after ordering.

---

## 7. Step 6 — dbt Marts (Star Schema)

**Location:** [`dbt/models/marts/`](file:///c:/Users/user/Desktop/projects/dbt/models/marts)

### What is a Star Schema?

```
           dim_customer
                │
dim_date ─── fact_orders ─── dim_product
                │
           dim_seller
```

- **Dimension tables** = descriptive context (who, what, when, where)
- **Fact table** = measurable events + all the foreign keys pointing to dimensions

This structure makes dashboards and queries extremely fast and simple.

### [`dim_customer.sql`](file:///c:/Users/user/Desktop/projects/dbt/models/marts/dim_customer.sql)

**Problem:** In Olist, the same real person gets a new `customer_id` for every order. The actual person identifier is `customer_unique_id`.

**Solution:** De-duplicate to one row per real person:

```sql
with ranked as (
    select *,
        row_number() over (
            partition by customer_unique_id
            order by customer_id desc   -- latest = most recent order
        ) as rn
    from stg_customers
)
select customer_unique_id as customer_key, city, state
from ranked where rn = 1
```

### [`dim_product.sql`](file:///c:/Users/user/Desktop/projects/dbt/models/marts/dim_product.sql)

Joins products with English category names + adds a derived **volumetric weight**:

```sql
select
    p.product_id as product_key,
    coalesce(t.category_name_english, 'unknown') as category_name_english,
    round((length_cm * width_cm * height_cm) / 5000.0, 2) as volumetric_weight_kg
from stg_products p
left join stg_category_translation t using (product_category_name)
```

> `coalesce(x, 'unknown')` returns `x` if not null, `'unknown'` otherwise. Handles 610 uncategorized products.

### [`dim_date.sql`](file:///c:/Users/user/Desktop/projects/dbt/models/marts/dim_date.sql)

Generated entirely in SQL — no CSV needed:

```sql
with date_spine as (
    select generate_series(
        '2016-01-01'::date, '2019-12-31'::date, '1 day'
    )::date as date_day
)
select
    date_day               as date_key,
    extract(year  from date_day) as year,
    extract(month from date_day) as month,
    extract(dow   from date_day) as day_of_week,  -- 0=Sun, 6=Sat
    (extract(dow from date_day) in (0, 6)) as is_weekend,
    to_char(date_day, 'YYYY-MM')   as year_month
from date_spine
```

### [`fact_orders.sql`](file:///c:/Users/user/Desktop/projects/dbt/models/marts/fact_orders.sql)

The central fact table — one row per order. Contains all metrics + foreign keys to dimensions:

```sql
select
    -- Foreign keys to dimensions
    o.order_id,
    c.customer_unique_id        as customer_key,
    o.purchase_ts::date         as purchase_date_key,   -- joins dim_date

    -- Delivery performance metrics (derived in SQL)
    (o.delivered_customer_ts < o.estimated_delivery_ts) as delivered_on_time,
    extract(epoch from (delivered_customer_ts - purchase_ts))
        / 86400.0               as order_to_delivery_days,

    -- Revenue from intermediate
    i.revenue, i.gmv, i.item_count,

    -- Payment from intermediate
    p.total_payment_value, p.primary_payment_type,

    -- Review from intermediate
    r.review_score

from stg_orders o
left join stg_customers           c on o.customer_id = c.customer_id
left join int_orders_items_agg    i on o.order_id    = i.order_id
left join int_orders_payments_agg p on o.order_id    = p.order_id
left join int_orders_reviews_dedup r on o.order_id   = r.order_id
```

> All joins are `LEFT JOIN` so orders without payments/reviews/items are still included.

---

## 8. Step 7 — Warehouse Loading

**File:** [`ingestion/load_to_warehouse.py`](file:///c:/Users/user/Desktop/projects/ingestion/load_to_warehouse.py)

### The problem

After Steps 1–2, we have clean Parquet files sitting in `data/processed/`. But dbt runs SQL transformations **inside PostgreSQL**. We need to push the data from local files into database tables.

This is the bridge:

```
data/processed/*.parquet  →  [load_to_warehouse.py]  →  PostgreSQL tables
```

### How it works

```python
def load_parquet_to_table(parquet_path, engine):
    table_name = parquet_path.stem  # e.g. "olist_orders_dataset"
    df = pd.read_parquet(parquet_path)

    # 'replace' = drop and recreate the table on every run
    # This is the simplest strategy for a daily-refresh pipeline
    df.to_sql(
        name=table_name,
        con=engine,
        schema="public",
        if_exists="replace",   # full refresh each time
        index=False,
        method="multi",        # batch inserts for speed
        chunksize=5000,
    )
```

### Key concepts introduced

| Concept | What it means |
|---|---|
| **SQLAlchemy engine** | Python object that manages the database connection pool |
| **`to_sql()`** | pandas method that writes a DataFrame directly into a database table |
| **`if_exists='replace'`** | Drop the table and recreate it on every run (full refresh) |
| **`method='multi'`** | Send multiple rows per INSERT statement (faster than one-by-one) |
| **`chunksize=5000`** | Process 5000 rows at a time to avoid memory issues with large tables |
| **`WAREHOUSE_URL`** | Environment variable holding the connection string — keeps credentials out of code |

### Connection string anatomy

```
postgresql://postgres:postgres@warehouse:5432/warehouse
│            │        │        │         │    │
protocol     user     password host      port database
```

- Inside Docker: host = `warehouse` (the docker-compose service name)
- Locally: host = `localhost`

### Run it

```bash
# Requires a running PostgreSQL instance
python ingestion/load_to_warehouse.py
```

---

## 9. Step 8 — Orchestration (Airflow + Docker)

### The problem

We have 5 scripts that must run **in order**, every day:
1. `extract.py` — download from Kaggle
2. `load.py` — validate and convert to Parquet
3. `load_to_warehouse.py` — push into PostgreSQL
4. `dbt run` — build all SQL models
5. `dbt test` — run all schema tests

Running these manually is error-prone. **Airflow** automates this.

### What is Airflow?

Apache Airflow is an **orchestrator** — it defines and runs sequences of tasks (called a DAG) on a schedule. Think of it as a smart cron job with:
- A web UI to monitor runs
- Automatic retries on failure
- Task dependency management (Task B waits for Task A)
- Logs for every run

### The DAG

**File:** [`orchestration/dags/pipeline_dag.py`](file:///c:/Users/user/Desktop/projects/orchestration/dags/pipeline_dag.py)

```python
with DAG(
    dag_id="business_analytics_pipeline",
    schedule="@daily",          # runs once per day
    catchup=False,              # don't backfill past dates
) as dag:

    extract              = BashOperator(task_id="extract",              ...)
    validate_and_parquet = BashOperator(task_id="validate_and_parquet", ...)
    load_to_warehouse    = BashOperator(task_id="load_to_warehouse",    ...)
    dbt_run              = BashOperator(task_id="dbt_run",              ...)
    dbt_test             = BashOperator(task_id="dbt_test",             ...)

    extract >> validate_and_parquet >> load_to_warehouse >> dbt_run >> dbt_test
```

The `>>` operator means "must complete before". This creates the flow:

```
extract → validate_and_parquet → load_to_warehouse → dbt_run → dbt_test
```

If any step fails, Airflow retries it (up to 2 times), then marks the run as failed.

### Docker Compose — the full stack

**File:** [`docker-compose.yml`](file:///c:/Users/user/Desktop/projects/docker-compose.yml)

Docker Compose runs **5 services** in containers:

| Service | Container | What it does |
|---|---|---|
| `warehouse` | postgres:16 | PostgreSQL database (stores raw tables + dbt models) |
| `airflow-init` | airflow:2.9.3 | One-time setup: creates Airflow DB + admin user |
| `airflow-webserver` | airflow:2.9.3 | Web UI at http://localhost:8080 |
| `airflow-scheduler` | airflow:2.9.3 | Picks up and runs DAG tasks on schedule |
| `dashboard` | custom build | Streamlit at http://localhost:8501 |
| `api` | custom build | FastAPI at http://localhost:8000 |

### How Docker Compose works

```yaml
# Shared config reused by all Airflow containers
x-airflow-common: &airflow-common
  image: apache/airflow:2.9.3-python3.11
  environment:
    WAREHOUSE_URL: postgresql://postgres:postgres@warehouse:5432/warehouse
  volumes:
    - ./ingestion:/opt/airflow/ingestion   # mount local code into container
    - ./dbt:/opt/airflow/dbt
    - ./data:/opt/airflow/data
  depends_on:
    warehouse:
      condition: service_healthy   # wait for Postgres to be ready
```

Key ideas:
- **YAML anchors** (`&airflow-common` / `<<: *airflow-common`) — avoid repeating the same config for 3 Airflow containers
- **Volumes** — mount your local code into the container so changes are reflected without rebuilding
- **`depends_on: service_healthy`** — the scheduler waits for Postgres to pass its health check before starting
- **`_PIP_ADDITIONAL_REQUIREMENTS`** — installs extra Python packages inside the Airflow containers at startup

### The `init-multiple-dbs.sh` script

**File:** [`scripts/init-multiple-dbs.sh`](file:///c:/Users/user/Desktop/projects/scripts/init-multiple-dbs.sh)

Postgres starts with one database by default. This script creates **two**:
- `warehouse` — your data warehouse (dbt models live here)
- `airflow` — Airflow's internal metadata database

It also creates a dedicated `airflow` Postgres role, so Airflow doesn't use the superuser.

### Start everything

```bash
docker compose up -d   # -d = detached (runs in background)
```

To see logs:
```bash
docker compose logs -f airflow-scheduler   # follow scheduler logs
docker compose logs warehouse              # check Postgres started OK
```

To stop everything:
```bash
docker compose down        # stop containers, keep data
docker compose down -v     # stop containers AND delete all data volumes
```

---

## 10. Key Concepts Glossary

| Term | Plain English |
|---|---|
| **ETL** | Extract, Transform, Load — classic pipeline pattern |
| **ELT** | Extract, Load, Transform — modern: load raw first, transform in-warehouse |
| **Parquet** | A fast, compact columnar file format for analytics |
| **dbt** | Tool to write, run, test and document SQL transformations |
| **Staging** | First dbt layer — clean and rename raw columns, no joins |
| **Intermediate** | Second dbt layer — aggregations and joins, not yet business-ready |
| **Mart** | Final dbt layer — business-ready tables for dashboards |
| **Star Schema** | Fact table at the center, dimension tables around it |
| **Fact table** | Measurable events and numbers (e.g. orders, revenue) |
| **Dimension table** | Descriptive attributes (who, what, when, where) |
| **GMV** | Gross Merchandise Value — total value of goods sold |
| **RFM** | Recency, Frequency, Monetary — customer segmentation model |
| **DAG** | Directed Acyclic Graph — how Airflow organises pipeline tasks |
| **Materialized** | A dbt model stored as a table (vs a view computed on the fly) |
| **Schema test** | An assertion dbt checks after running (e.g. `unique`, `not_null`) |
| **Primary key** | Column(s) that uniquely identify a row in a table |
| **Foreign key** | Column that references the primary key of another table |
| **Coalesce** | SQL function: returns the first non-null value from a list |
| **SQLAlchemy** | Python library for connecting to databases via a unified API |
| **Docker** | Packages an application + its dependencies into a portable container |
| **Docker Compose** | Runs multiple Docker containers together as a single stack |
| **Volume** | Persistent storage that survives container restarts |
| **YAML anchor** | Reusable config block in YAML (`&name` to define, `*name` to reference) |
| **Health check** | A command Docker runs periodically to check if a service is ready |
| **DISTINCT ON** | PostgreSQL: keep one row per group (similar to `GROUP BY` but keeps all columns) |

---

## 11. How to Run Everything

### Prerequisites

```bash
pip install kaggle pandas pyarrow
```

### Step 1 — Download raw data

```bash
python ingestion/extract.py
# Prompts for Kaggle username + API key on first run → saves to ~/.kaggle/kaggle.json
```

### Step 2 — Validate and convert to Parquet

```bash
python ingestion/load.py
# Output: data/processed/*.parquet (9 files)
```

### Step 3 — Load into PostgreSQL

```bash
python ingestion/load_to_warehouse.py
# Reads data/processed/*.parquet → creates tables in PostgreSQL
# Requires a running Postgres (either local or via docker compose up warehouse)
```

### Step 4 — Start the full Docker stack

```bash
docker compose up -d
```

| Service | URL | Credentials |
|---|---|---|
| Airflow UI | http://localhost:8080 | admin / admin |
| Streamlit Dashboard | http://localhost:8501 | — |
| FastAPI docs | http://localhost:8000/docs | — |
| PostgreSQL | localhost:5432 | postgres / postgres |

### Step 5 — Run dbt manually

```bash
# One-time: copy the example dbt connection profile
cp dbt/profiles.yml.example ~/.dbt/profiles.yml

cd dbt
dbt run          # build all models (staging → intermediate → marts)
dbt test         # run all schema tests
dbt docs generate
dbt docs serve   # browse docs at http://localhost:8080
```

---

## 12. What Comes Next

| Week | Work | Status |
|---|---|---|
| 1 | Kaggle ingestion scripts (extract + load) | ✅ Done |
| 1 | Repo scaffolding + Git + README | ✅ Done |
| 2 | dbt staging models (all 9 source tables) | ✅ Done |
| 2 | dbt intermediate + marts (full star schema) | ✅ Done |
| 3 | Warehouse loading (Parquet → PostgreSQL) | ✅ Done |
| 3 | Airflow DAG + Docker Compose wiring | ✅ Done |
| 4 | Streamlit KPI dashboard (revenue, delivery time, RFM segments) | 🔜 Next |
| 5 | Demand forecasting (Prophet baseline + LSTM backtesting) | 🔜 |
| 6 | FastAPI model serving + GitHub Actions CI | 🔜 |

### Full data lineage at a glance

```
Kaggle API
    │  [ingestion/extract.py]
    ▼
data/raw/*.csv (9 CSVs)
    │  [ingestion/load.py + schemas.py]
    ▼
data/processed/*.parquet (9 Parquet files)
    │  [ingestion/load_to_warehouse.py]
    ▼
PostgreSQL tables (public.olist_orders_dataset, etc.)
    │  [dbt staging — 8 models]
    ▼
stg_orders, stg_customers, stg_order_items,
stg_order_payments, stg_order_reviews,
stg_products, stg_sellers, stg_category_translation
    │  [dbt intermediate — 3 models]
    ▼
int_orders_items_agg       → order revenue, GMV, item count
int_orders_payments_agg    → total payment value, payment type flags
int_orders_reviews_dedup   → one clean review per order
    │  [dbt marts — 5 tables]
    ▼
dim_customer    → one row per unique person
dim_product     → product catalogue + English categories + volumetric weight
dim_seller      → seller master with location
dim_date        → calendar spine 2016–2019
fact_orders     → central fact: one row per order with ALL metrics
    │
    ├──▶ Streamlit Dashboard (KPIs, charts, filters)
    └──▶ FastAPI Prediction API (demand forecasts)

All 5 steps orchestrated daily by Airflow DAG via Docker Compose.
```
