"""
pipeline_dag.py

Daily pipeline: extract → validate+parquet → load to warehouse → dbt run → dbt test.
Placed in orchestration/dags/, mounted into the Airflow container's DAGs folder
by docker-compose.yml.

Task flow:
    extract  →  validate_and_parquet  →  load_to_warehouse  →  dbt_run  →  dbt_test
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "moustafa",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# Connection string for the warehouse — matches docker-compose.yml service name "warehouse"
WAREHOUSE_URL = "postgresql://postgres:postgres@warehouse:5432/warehouse"

with DAG(
    dag_id="business_analytics_pipeline",
    description="Ingest Olist data, transform with dbt, refresh marts",
    default_args=default_args,
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["business-analytics", "portfolio"],
) as dag:

    # 1. Download raw CSVs from Kaggle → data/raw/
    extract = BashOperator(
        task_id="extract",
        bash_command="cd /opt/airflow && python ingestion/extract.py",
    )

    # 2. Validate schemas + convert to Parquet → data/processed/
    validate_and_parquet = BashOperator(
        task_id="validate_and_parquet",
        bash_command="cd /opt/airflow && python ingestion/load.py",
    )

    # 3. Load Parquet files into PostgreSQL warehouse tables
    load_to_warehouse = BashOperator(
        task_id="load_to_warehouse",
        bash_command="cd /opt/airflow && python ingestion/load_to_warehouse.py",
        env={"WAREHOUSE_URL": WAREHOUSE_URL},
        append_env=True,
    )

    # 4. Run dbt models: staging → intermediate → marts
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt && dbt run --profiles-dir .",
    )

    # 5. Run dbt schema tests
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt && dbt test --profiles-dir .",
    )

    extract >> validate_and_parquet >> load_to_warehouse >> dbt_run >> dbt_test
