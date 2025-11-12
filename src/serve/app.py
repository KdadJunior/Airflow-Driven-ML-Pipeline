from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict, List

import mlflow
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.responses import PlainTextResponse

MODEL_NAME = os.getenv("MODEL_NAME", "imdb_sentiment")
MODEL_STAGE = os.getenv("MODEL_STAGE", "Production")

app = FastAPI(title="IMDb Sentiment Service", version="0.1.0")

REQUEST_COUNT = Counter("prediction_requests_total", "Total prediction requests")
REQUEST_LATENCY = Histogram("prediction_latency_seconds", "Prediction latency in seconds")
ERROR_COUNT = Counter("prediction_errors_total", "Prediction errors")
MODEL_VERSION = Gauge("model_version_info", "Current model version", ["version"])


class TextPayload(BaseModel):
    text: str = Field(..., min_length=3)


class BatchPayload(BaseModel):
    inputs: List[TextPayload]


class PredictionResponse(BaseModel):
    probabilities: List[float]
    labels: List[int]
    model_version: str


def _load_model() -> mlflow.pyfunc.PyFuncModel:
    model_uri = f"models:/{MODEL_NAME}/{MODEL_STAGE}"
    model = mlflow.pyfunc.load_model(model_uri=model_uri)
    return model


@lru_cache
def get_model() -> mlflow.pyfunc.PyFuncModel:
    model = _load_model()
    version = model.metadata.run_id
    MODEL_VERSION.labels(version=version).set(1)
    return model


@app.get("/health")
def health() -> Dict[str, Any]:
    try:
        model = get_model()
        version = model.metadata.run_id
    except Exception as exc:  # noqa: BLE001
        return {"status": "unhealthy", "detail": str(exc)}
    return {"status": "ok", "model_version": version}


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: BatchPayload) -> PredictionResponse:
    if not payload.inputs:
        raise HTTPException(status_code=400, detail="inputs must not be empty")

    with REQUEST_LATENCY.time():
        REQUEST_COUNT.inc()
        try:
            model = get_model()
            texts = [item.text for item in payload.inputs]
            preds = model.predict(texts)
            if isinstance(preds, list):
                preds = np.array(preds)
            if preds.ndim == 1:
                probabilities = preds.tolist()
            else:
                probabilities = preds[:, 1].tolist()
            labels = (np.array(probabilities) >= 0.5).astype(int).tolist()
            return PredictionResponse(
                probabilities=probabilities,
                labels=labels,
                model_version=model.metadata.run_id,
            )
        except Exception as exc:  # noqa: BLE001
            ERROR_COUNT.inc()
            raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    data = generate_latest()
    return PlainTextResponse(data.decode("utf-8"), media_type="text/plain; version=0.0.4")


