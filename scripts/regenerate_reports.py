#!/usr/bin/env python3
"""
Regenerate confusion matrix and reliability curve from the current combined model
and combined dataset, using the same 80/20 stratified split as training.

Use this to update reports without retraining. Run from project root.
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from ml_pipeline import config
from ml_pipeline.evaluation import plot_confusion_matrix, plot_reliability_curve


def main() -> None:
    if not config.COMBINED_DATA_PATH.exists():
        print(f"Error: {config.COMBINED_DATA_PATH.name} not found.")
        sys.exit(1)

    model_path = config.MODELS_DIR / "career_predictor.pkl"
    encoder_path = config.LABEL_ENCODER_PATH
    if not model_path.exists() or not encoder_path.exists():
        print("Error: career_predictor.pkl or label_encoder.pkl not found. Train first.")
        sys.exit(1)

    encoder = joblib.load(encoder_path)
    class_names = encoder.classes_.tolist()

    df = pd.read_csv(config.COMBINED_DATA_PATH)
    df = df[df["career"].isin(encoder.classes_)].copy()
    feature_cols = [c for c in df.columns if c not in ("career", "course_name")]
    X = df[feature_cols].to_numpy(dtype=np.float64)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    y = encoder.transform(df["career"])

    # Same split as train_combined_model.py
    _, X_holdout, _, y_holdout = train_test_split(
        X, y,
        test_size=0.2,
        stratify=y,
        random_state=config.RANDOM_SEED,
    )

    model = joblib.load(model_path)

    holdout_proba = model.predict_proba(X_holdout)
    holdout_pred = holdout_proba.argmax(axis=1)

    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    plot_confusion_matrix(
        y_holdout, holdout_pred,
        label_names=class_names,
        output_path=config.REPORTS_DIR / "confusion_matrix.png",
    )
    plot_reliability_curve(y_holdout, holdout_proba, config.REPORTS_DIR / "reliability_curve.png")

    print("Reports updated:")
    print(f"  {config.REPORTS_DIR / 'confusion_matrix.png'}")
    print(f"  {config.REPORTS_DIR / 'reliability_curve.png'}")


if __name__ == "__main__":
    main()
