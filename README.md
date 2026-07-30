# Business Analytics & Demand Forecasting Pipeline

End-to-end data platform on the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce):
ingestion → transformation (dbt) → orchestration (Airflow) → BI dashboard (Streamlit) →
demand forecasting & customer segmentation → prediction API (FastAPI).

## Architecture

```
Kaggle API
    │  [extract.py]
    ▼
data/raw/*.csv (9 CSVs)
    │  [load.py — validate schemas]
    ▼
data/processed/*.parquet
    │  [load_to_warehouse.py — push to Postgres]
    ▼
PostgreSQL (warehouse DB)
    │  [dbt — staging → intermediate → marts]
    ▼
Star Schema: fact_orders + dim_customer, dim_product, dim_seller, dim_date
    │
    ├──▶ Streamlit KPI Dashboard
    └──▶ FastAPI Prediction API

Orchestrated daily by Airflow DAG. All services run via Docker Compose.
```

## Repo structure

```
├── ingestion/              # Python ingestion scripts
│   ├── extract.py          #   Kaggle download + extraction
│   ├── load.py             #   Schema validation + CSV → Parquet
│   ├── load_to_warehouse.py#   Parquet → PostgreSQL tables
│   └── schemas.py          #   Expected column definitions per CSV
├── dbt/                    # SQL transformation (star schema)
│   ├── models/
│   │   ├── staging/        #   8 models: raw → clean (rename, cast)
│   │   ├── intermediate/   #   3 models: aggregations + dedup
│   │   └── marts/          #   5 models: fact_orders + 4 dimensions
│   ├── dbt_project.yml
│   ├── profiles.yml        #   Docker-ready connection profile
│   └── profiles.yml.example#   Template for local development
├── orchestration/dags/     # Airflow DAG
│   └── pipeline_dag.py     #   extract → validate → warehouse → dbt run → dbt test
├── dashboard/              # Streamlit app + Dockerfile
│   └── app.py
├── api/                    # FastAPI prediction service + Dockerfile
│   └── main.py
├── modeling/               # Notebooks: RFM segmentation + forecasting (WIP)
├── scripts/
│   └── init-multiple-dbs.sh#   Postgres entrypoint: creates warehouse + airflow DBs
├── data/
│   ├── raw/                #   Downloaded CSVs (gitignored)
│   └── processed/          #   Validated Parquet files (gitignored)
├── docker-compose.yml      #   Full stack: Postgres, Airflow, Streamlit, FastAPI
├── requirements.txt
├── PROJECT_GUIDE.md        #   Comprehensive learning guide for the project
└── README.md
```

## Quickstart

**1. Get Kaggle credentials**
Download `kaggle.json` from kaggle.com → Settings → API, then:
```bash
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json
```
Or just run `python ingestion/extract.py` — it will prompt you interactively.

**2. Run ingestion locally (before Docker)**
```bash
pip install -r requirements.txt

python ingestion/extract.py          # download from Kaggle
python ingestion/load.py             # validate schemas → Parquet
python ingestion/load_to_warehouse.py  # Parquet → PostgreSQL (requires running Postgres)
```

**3. Bring up the full stack**
```bash
docker compose up -d
```
| Service | URL | Credentials |
|---|---|---|
| Airflow UI | http://localhost:8080 | admin / admin |
| Dashboard | http://localhost:8501 | — |
| API docs | http://localhost:8000/docs | — |
| PostgreSQL | localhost:5432 | postgres / postgres |

**4. Run dbt**
```bash
cd dbt
cp profiles.yml.example ~/.dbt/profiles.yml   # adjust host if outside Docker
dbt run          # build all models
dbt test         # run schema tests
dbt docs generate && dbt docs serve
```

## Status

- [x] Ingestion (extract + schema-validated load to Parquet)
- [x] Warehouse loading (Parquet → PostgreSQL)
- [x] Repo scaffolding, Docker Compose, .gitignore
- [x] dbt staging (8 models for all 9 source tables)
- [x] dbt intermediate (3 aggregation/dedup models)
- [x] dbt marts — full star schema (fact_orders + 4 dimensions)
- [x] Airflow DAG (5-step pipeline: extract → validate → warehouse → dbt run → dbt test)
- [x] Streamlit KPI dashboard (revenue, delivery time, RFM segments)
- [ ] Demand forecasting model (Prophet baseline + LSTM)
- [ ] FastAPI model serving wired to trained model

## Why this project

Built to demonstrate data engineering (ingestion, orchestration, transformation),
data analysis (KPIs, segmentation), and modeling (time-series forecasting with
proper walk-forward backtesting) in a single, reproducible, containerized pipeline
rather than three disconnected notebooks.
