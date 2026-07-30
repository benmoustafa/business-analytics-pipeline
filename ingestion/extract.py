"""
ingestion/extract.py

Downloads the Olist Brazilian E-Commerce dataset from Kaggle and extracts
the raw CSV files into data/raw/.

Requires a Kaggle API token (kaggle.json) placed in ~/.kaggle/ or set via
the KAGGLE_USERNAME / KAGGLE_KEY environment variables.
See: https://www.kaggle.com/docs/api#authentication

Usage:
    python ingestion/extract.py
"""

import logging
import os
import zipfile
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DATASET_SLUG = "olistbr/brazilian-ecommerce"
RAW_DATA_DIR = Path("data/raw")
ZIP_PATH = RAW_DATA_DIR / "brazilian-ecommerce.zip"


def _kaggle_credentials_available() -> bool:
    """Check whether Kaggle API credentials are configured."""
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    env_creds = os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY")
    return kaggle_json.exists() or bool(env_creds)


def setup_kaggle_credentials() -> None:
    """Prompt for Kaggle API credentials and write ~/.kaggle/kaggle.json if missing."""
    if _kaggle_credentials_available():
        return

    logger.info("Kaggle API credentials not configured. Please enter your credentials:")
    username = input("Kaggle Username: ").strip()
    key = input("Kaggle API Key: ").strip()

    if not username or not key:
        logger.error("Both username and API key are required.")
        raise SystemExit(1)

    kaggle_dir = Path.home() / ".kaggle"
    kaggle_dir.mkdir(parents=True, exist_ok=True)
    
    import json
    kaggle_json = kaggle_dir / "kaggle.json"
    with open(kaggle_json, "w") as f:
        json.dump({"username": username, "key": key}, f)
        
    logger.info("Credentials saved to %s", kaggle_json)


def download_dataset() -> None:
    """Download the dataset zip from Kaggle using the Kaggle API."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    setup_kaggle_credentials()

    if not _kaggle_credentials_available():
        logger.error(
            "No Kaggle API credentials found. Either:\n"
            "  1) Place kaggle.json in ~/.kaggle/ (download it from "
            "     https://www.kaggle.com/settings > API > Create New Token), or\n"
            "  2) Set KAGGLE_USERNAME and KAGGLE_KEY environment variables.\n"
            "Alternatively, manually download the dataset from "
            "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce "
            "and place the CSV files in data/raw/."
        )
        raise SystemExit(1)

    from kaggle.api.kaggle_api_extended import KaggleApi  # imported lazily

    api = KaggleApi()
    api.authenticate()

    logger.info("Downloading dataset '%s' ...", DATASET_SLUG)
    api.dataset_download_files(DATASET_SLUG, path=str(RAW_DATA_DIR), quiet=False)
    logger.info("Download complete.")


def extract_zip() -> None:
    """Extract all CSV files from the downloaded zip archive."""
    zip_files = list(RAW_DATA_DIR.glob("*.zip"))
    if not zip_files:
        logger.warning("No zip file found in %s — skipping extraction.", RAW_DATA_DIR)
        return

    for zip_path in zip_files:
        logger.info("Extracting %s ...", zip_path.name)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(RAW_DATA_DIR)
        zip_path.unlink()  # remove zip after extraction to keep data/raw/ clean

    logger.info("Extraction complete. Files available in %s", RAW_DATA_DIR)


def verify_files() -> None:
    """List extracted CSV files and warn if the expected count looks off."""
    csv_files = sorted(RAW_DATA_DIR.glob("*.csv"))
    logger.info("Found %d CSV file(s) in %s:", len(csv_files), RAW_DATA_DIR)
    for f in csv_files:
        size_mb = f.stat().st_size / (1024 * 1024)
        logger.info("  - %s (%.2f MB)", f.name, size_mb)

    if len(csv_files) < 9:
        logger.warning(
            "Expected 9 CSV files for the full Olist dataset, found %d. "
            "Check the download/extraction step.",
            len(csv_files),
        )


def main() -> None:
    download_dataset()
    extract_zip()
    verify_files()


if __name__ == "__main__":
    main()
