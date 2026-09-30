"""FastAPI application for the AI severity-prediction service."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from . import __version__
from .model import model
from .schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
    InspectionFeatures,
    Prediction,
    TrainRequest,
    TrainResponse,
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if not model.load():
        model.train(samples=1500, seed=42)
    yield


app = FastAPI(
    title="Inspection AI Service",
    version=__version__,
    description="Predicts defect severity from inspection measurements.",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    if not model.is_loaded:
        return HealthResponse(
            status="degraded", model_loaded=False, model_version=None, version=__version__
        )
    return HealthResponse(
        status="ok",
        model_loaded=True,
        model_version=model.version,
        version=__version__,
    )


@app.post("/predict", response_model=Prediction, tags=["inference"])
def predict(features: InspectionFeatures) -> Prediction:
    if not model.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded",
        )
    return model.predict(features)


@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["inference"])
def predict_batch(payload: BatchPredictionRequest) -> BatchPredictionResponse:
    if not model.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded",
        )
    return BatchPredictionResponse(
        predictions=[model.predict(item) for item in payload.items]
    )


@app.post("/train", response_model=TrainResponse, tags=["mlops"])
def train(payload: TrainRequest) -> TrainResponse:
    report = model.train(samples=payload.samples, seed=payload.seed)
    return TrainResponse(**vars(report))
