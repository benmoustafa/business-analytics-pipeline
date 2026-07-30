# Business Analytics & Demand Forecasting Pipeline

End-to-end data platform on the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce):
ingestion → transformation (dbt) → orchestration (Airflow) → BI dashboard (Streamlit) →
demand forecasting & customer segmentation → prediction API (FastAPI).

## Architecture

```
Kaggle CSVs -> extract.py -> load.py -> Postgres (raw) -> dbt (staging/intermediate/marts)
                                                              |
                                    ------------------------------------------
                                    |                                        |
                            Streamlit dashboard                      Forecasting model -> FastAPI
```

Orchestrated end-to-end by an Airflow DAG (`orchestration/dags/pipeline_dag.py`).

## Repo structure

```
├── ingestion/          # extract.py (Kaggle download), load.py (validate + Parquet), schemas.py
├── dbt/                # star schema: staging -> intermediate -> marts
├── orchestration/dags/ # Airflow DAG wiring ingestion + dbt together
├── dashboard/          # Streamlit app + Dockerfile
├── modeling/           # RFM segmentation + demand forecasting notebooks (WIP)
├── api/                # FastAPI service serving model predictions
├── scripts/            # Postgres init script (multiple DBs)
├── docker-compose.yml  # warehouse, Airflow, dashboard, API
└── data/                # raw/ and processed/ (gitignored, populated by ingestion)
```

## Quickstart

**1. Get Kaggle credentials**
Download `kaggle.json` from kaggle.com → Settings → API, then:
```bash
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json
```

**2. Run ingestion locally (before wiring into Airflow)**
```bash
cd ingestion
pip install -r requirements.txt
python extract.py
python load.py
```

**3. Bring up the full stack**
```bash
docker compose up -d
```
- Airflow UI: http://localhost:8080 (user: `admin` / pass: `admin`)
- Dashboard: http://localhost:8501
- API: http://localhost:8000/docs

**4. Run dbt**
```bash
cd dbt
cp profiles.yml.example ~/.dbt/profiles.yml   # adjust host to "warehouse" if running inside Docker
dbt run
dbt test
```

## Status

- [x] Ingestion (extract + schema-validated load to Parquet)
- [x] Repo scaffolding, Docker Compose, first dbt staging model
- [ ] Full star schema (intermediate + marts)
- [ ] Streamlit KPI dashboard (revenue, delivery time, RFM segments)
- [ ] Demand forecasting model (Prophet baseline + LSTM)
- [ ] FastAPI model serving wired to trained model

## Why this project

Built to demonstrate data engineering (ingestion, orchestration, transformation),
data analysis (KPIs, segmentation), and modeling (time-series forecasting with
proper walk-forward backtesting) in a single, reproducible, containerized pipeline
rather than three disconnected notebooks.
