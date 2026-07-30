"""
Loads validated Parquet files from data/processed/ into PostgreSQL warehouse tables.

Usage:
    python ingestion/load_to_warehouse.py
"""

import logging
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

PROCESSED_DATA_DIR = Path("data/processed")

WAREHOUSE_URL = os.environ.get(
    "WAREHOUSE_URL",
    "postgresql://postgres:postgres@localhost:5432/warehouse",
)


def get_engine():
    """Create a SQLAlchemy engine from the warehouse URL."""
    logger.info("Connecting to warehouse: %s", WAREHOUSE_URL.split("@")[-1])  # log host only
    engine = create_engine(WAREHOUSE_URL)
    # Test the connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Connection successful.")
    return engine


def load_parquet_to_table(parquet_path: Path, engine) -> None:
    """Load a single Parquet file into a PostgreSQL table.

    The table name is derived from the filename:
        olist_orders_dataset.parquet → olist_orders_dataset
    """
    table_name = parquet_path.stem  # filename without extension

    logger.info("Loading %s → public.%s ...", parquet_path.name, table_name)
    df = pd.read_parquet(parquet_path)

    # Use 'replace' to fully refresh the table on each run.
    # This is the simplest strategy and matches the daily-refresh pipeline design.
    df.to_sql(
        name=table_name,
        con=engine,
        schema="public",
        if_exists="replace",
        index=False,
        method="multi",       # batch inserts for speed
        chunksize=5000,
    )

    logger.info(
        "  ✓ %s loaded (%d rows, %d columns)",
        table_name, len(df), len(df.columns),
    )


def main() -> None:
    parquet_files = sorted(PROCESSED_DATA_DIR.glob("*.parquet"))

    if not parquet_files:
        logger.error(
            "No Parquet files found in %s. Run 'python ingestion/load.py' first.",
            PROCESSED_DATA_DIR,
        )
        raise SystemExit(1)

    engine = get_engine()

    logger.info("Loading %d Parquet file(s) into the warehouse...", len(parquet_files))

    failures = []
    for pq in parquet_files:
        try:
            load_parquet_to_table(pq, engine)
        except Exception as e:
            logger.error("Failed to load %s: %s", pq.name, e)
            failures.append(pq.name)

    if failures:
        logger.error("Warehouse load completed with errors: %s", failures)
        raise SystemExit(1)

    logger.info(
        "All %d tables loaded successfully into %s",
        len(parquet_files),
        WAREHOUSE_URL.split("@")[-1],
    )


if __name__ == "__main__":
    main()
