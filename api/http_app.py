"""
HTTP inference API for Google Cloud Run.

Runs the same `predict()` logic as `predict.py` (CLI stdin/stdout).
Cloud Run sets PORT; Uvicorn listens on 0.0.0.0:$PORT.

Models load on first /predict (via predict() -> load_models()), not at process
startup, so the container binds to PORT immediately and passes Cloud Run checks.
"""

from __future__ import annotations

import os
from typing import List

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from api.predict import predict

app = FastAPI(title="Career prediction API", version="0.1.0")

# Optional shared secret: set PREDICT_API_KEY in Cloud Run; send header X-Api-Key from clients.
_EXPECTED_API_KEY = os.environ.get("PREDICT_API_KEY", "").strip()


class ResponseItem(BaseModel):
    questionId: int
    answerIndex: int


class PredictRequest(BaseModel):
    responses: List[ResponseItem] = Field(..., min_length=30, max_length=30)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
async def predict_endpoint(request: Request, body: PredictRequest) -> dict:
    if _EXPECTED_API_KEY:
        sent = request.headers.get("x-api-key", "")
        if sent != _EXPECTED_API_KEY:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")

    raw = [r.model_dump() for r in body.responses]
    try:
        predictions = predict(raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {"predictions": predictions}
