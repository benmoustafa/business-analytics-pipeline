"""
main.py

FastAPI service exposing demand-forecast predictions.
Placeholder endpoint — wire up the trained model from modeling/ once it exists.
"""

import os

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Business Analytics — Prediction API")

WAREHOUSE_URL = os.environ.get("WAREHOUSE_URL", "")


class ForecastRequest(BaseModel):
    category: str
    horizon_days: int = 7


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/forecast")
def forecast(req: ForecastRequest) -> dict:
    # TODO: load the trained model (modeling/demand_forecasting.ipynb output)
    # and return real predictions per category/horizon.
    return {
        "category": req.category,
        "horizon_days": req.horizon_days,
        "predictions": [],
        "note": "placeholder — model not wired up yet",
    }
