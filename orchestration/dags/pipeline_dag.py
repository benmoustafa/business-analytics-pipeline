"""
pipeline_dag.py

Daily pipeline: extract -> load -> dbt run -> dbt test.
Placed in orchestration/dags/, mounted into the Airflow container's DAGs folder
by docker-compose.yml.
"""

from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "moustafa",
    "retries": 2,
}

with DAG(
    dag_id="business_analytics_pipeline",
    description="Ingest Olist data, transform with dbt, refresh marts",
    default_args=default_args,
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["business-analytics", "portfolio"],
) as dag:

    extract = BashOperator(
        task_id="extract",
        bash_command="cd /opt/airflow/ingestion && python extract.py",
    )

    load = BashOperator(
        task_id="load",
        bash_command="cd /opt/airflow/ingestion && python load.py",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt && dbt run",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt && dbt test",
    )

    extract >> load >> dbt_run >> dbt_test
