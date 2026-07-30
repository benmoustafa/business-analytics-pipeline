"""
ingestion/load.py

Validates the raw Olist CSV files against the expected schema (schemas.py),
runs basic data-quality checks (missing columns, nulls, duplicate keys),
and writes clean Parquet files to data/processed/.

Usage:
    python ingestion/load.py
"""

import logging
from pathlib import Path

import pandas as pd

from schemas import DATASET_SCHEMAS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")


class SchemaValidationError(Exception):
    """Raised when a raw CSV does not match its expected schema."""


def validate_columns(df: pd.DataFrame, expected_columns: list[str], filename: str) -> None:
    """Check that all expected columns are present in the dataframe."""
    missing = set(expected_columns) - set(df.columns)
    if missing:
        raise SchemaValidationError(
            f"{filename}: missing expected columns: {sorted(missing)}"
        )

    extra = set(df.columns) - set(expected_columns)
    if extra:
        logger.warning("%s: unexpected extra columns found: %s", filename, sorted(extra))


def check_data_quality(df: pd.DataFrame, primary_key: list[str], filename: str) -> None:
    """Log null counts and check for duplicate primary keys."""
    null_counts = df.isnull().sum()
    null_cols = null_counts[null_counts > 0]
    if not null_cols.empty:
        logger.info("%s: null values found ->\n%s", filename, null_cols.to_string())

    if primary_key:
        n_duplicates = df.duplicated(subset=primary_key).sum()
        if n_duplicates > 0:
            logger.warning(
                "%s: %d duplicate row(s) found on primary key %s",
                filename, n_duplicates, primary_key,
            )


def process_file(filename: str, schema: dict) -> None:
    """Load, validate, and convert a single raw CSV to Parquet."""
    raw_path = RAW_DATA_DIR / filename
    if not raw_path.exists():
        logger.error("File not found: %s — skipping.", raw_path)
        return

    logger.info("Processing %s ...", filename)
    df = pd.read_csv(raw_path)

    validate_columns(df, schema["columns"], filename)
    check_data_quality(df, schema["primary_key"], filename)

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_name = filename.replace(".csv", ".parquet")
    output_path = PROCESSED_DATA_DIR / output_name
    df.to_parquet(output_path, index=False)

    logger.info(
        "%s -> %s (%d rows, %d columns)",
        filename, output_path, len(df), len(df.columns),
    )


def main() -> None:
    logger.info("Starting ingestion of %d dataset file(s)...", len(DATASET_SCHEMAS))

    failures = []
    for filename, schema in DATASET_SCHEMAS.items():
        try:
            process_file(filename, schema)
        except SchemaValidationError as e:
            logger.error(str(e))
            failures.append(filename)

    if failures:
        logger.error("Ingestion completed with errors in: %s", failures)
        raise SystemExit(1)

    logger.info("Ingestion completed successfully. Parquet files in %s", PROCESSED_DATA_DIR)


if __name__ == "__main__":
    main()
