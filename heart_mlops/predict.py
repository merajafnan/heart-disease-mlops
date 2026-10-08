"""Reusable model loading and inference functions."""

import os
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from heart_mlops.config import ARTIFACT_DIR, FEATURES


@lru_cache(maxsize=1)
def load_model():
    path = Path(os.getenv("MODEL_PATH", ARTIFACT_DIR / "model.joblib"))
    if not path.is_file():
        raise FileNotFoundError(f"Model not found at {path}. Run training first.")
    return joblib.load(path)


def predict_one(values: dict, model=None):
    missing = set(FEATURES) - set(values)
    if missing:
        raise ValueError(f"Missing features: {sorted(missing)}")
    frame = pd.DataFrame([{feature: values[feature] for feature in FEATURES}])
    fitted = model if model is not None else load_model()
    probability = float(fitted.predict_proba(frame)[0, 1])
    prediction = int(probability >= 0.5)
    return {
        "prediction": prediction,
        "heart_disease_probability": round(probability, 4),
        "confidence": round(max(probability, 1 - probability), 4),
        "label": "presence" if prediction else "absence",
    }

