#!/usr/bin/env python3
"""
Train the career predictor on the combined non-survey dataset.

Uses ``config.COMBINED_DATA_PATH`` / ``config.AUGMENTED_DATA_PATH`` (from merge and optional augment).
No questionnaire data, no DeBERTa embeddings - tabular features only.

Run merge_career_datasets.py first.
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import numpy as np
import optuna
import pandas as pd
import xgboost as xgb
import lightgbm as lgb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import accuracy_score, f1_score, top_k_accuracy_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_class_weight

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from ml_pipeline import config
from ml_pipeline.evaluation import plot_confusion_matrix, plot_reliability_curve
from ml_pipeline.utils import read_json, write_json, utc_timestamp


def _prepare_sample_weights(y: np.ndarray):
    classes = np.unique(y)
    weights = compute_class_weight("balanced", classes=classes, y=y)
    lookup = {cls: w for cls, w in zip(classes, weights)}
    return np.vectorize(lookup.get)(y)


def _evaluate_model(model, X, y):
    proba = model.predict_proba(X)
    preds = proba.argmax(axis=1)
    return {
        "top1": float(accuracy_score(y, preds)),
        "top3": float(top_k_accuracy_score(y, proba, k=3)),
        "macro_f1": float(f1_score(y, preds, average="macro")),
    }


def _tune_xgb(X, y, sample_weights, n_trials=15):
    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 150, 400),
            "max_depth": trial.suggest_int("max_depth", 4, 10),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "min_child_weight": trial.suggest_float("min_child_weight", 1.0, 8.0),
            "gamma": trial.suggest_float("gamma", 0.0, 5.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.1, 5.0),
        }
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=config.RANDOM_SEED)
        scores = []
        for train_idx, val_idx in skf.split(X, y):
            m = xgb.XGBClassifier(
                objective="multi:softprob",
                num_class=len(np.unique(y)),
                random_state=config.RANDOM_SEED,
                eval_metric="mlogloss",
                tree_method="hist",
                **params,
            )
            m.fit(
                X[train_idx], y[train_idx],
                sample_weight=sample_weights[train_idx],
                eval_set=[(X[val_idx], y[val_idx])],
                verbose=False,
            )
            proba = m.predict_proba(X[val_idx])
            scores.append(top_k_accuracy_score(y[val_idx], proba, k=3))
        return float(np.mean(scores))

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return study.best_params | {"best_score": study.best_value}


def _tune_lgb(X, y, sample_weights, n_trials=15):
    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 150, 400),
            "max_depth": trial.suggest_int("max_depth", -1, 12),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "min_child_samples": trial.suggest_int("min_child_samples", 5, 50),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.1, 5.0),
        }
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=config.RANDOM_SEED)
        scores = []
        for train_idx, val_idx in skf.split(X, y):
            m = lgb.LGBMClassifier(
                objective="multiclass",
                num_class=len(np.unique(y)),
                random_state=config.RANDOM_SEED,
                n_jobs=-1,
                **params,
            )
            m.fit(
                X[train_idx], y[train_idx],
                sample_weight=sample_weights[train_idx],
                eval_set=[(X[val_idx], y[val_idx])],
                callbacks=[lgb.early_stopping(25, verbose=False)],
            )
            proba = m.predict_proba(X[val_idx])
            scores.append(top_k_accuracy_score(y[val_idx], proba, k=3))
        return float(np.mean(scores))

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return study.best_params | {"best_score": study.best_value}


def main():
    data_path = (
        config.AUGMENTED_DATA_PATH
        if config.AUGMENTED_DATA_PATH.exists()
        else config.COMBINED_DATA_PATH
    )
    if not data_path.exists():
        print("Error: No training data found.")
        print("Run: python scripts/merge_career_datasets.py")
        print("Then: python scripts/augment_training_data.py  (recommended for questionnaire alignment)")
        sys.exit(1)

    print(f"Using training data: {data_path.name}")
    df = pd.read_csv(data_path)

    # Filter to target careers only
    df = df[df["career"].isin(config.TARGET_CAREERS)].copy()

    # Downsample dominant classes to reduce imbalance (CS had 21k, others ~1.8k)
    max_per_class = 3500
    counts = df["career"].value_counts()
    to_drop = []
    for career in counts.index:
        if counts[career] > max_per_class:
            excess = counts[career] - max_per_class
            idx = df[df["career"] == career].index
            drop_idx = np.random.RandomState(config.RANDOM_SEED).choice(idx, size=excess, replace=False)
            to_drop.extend(drop_idx)
    if to_drop:
        df = df.drop(index=to_drop).reset_index(drop=True)
        print(f"Downsampled to max {max_per_class} per class (dropped {len(to_drop)} rows)")

    feature_cols = [c for c in df.columns if c not in ("career", "course_name")]
    X = df[feature_cols].to_numpy(dtype=np.float64)
    # Handle any remaining NaN
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df["career"])

    sample_weights = _prepare_sample_weights(y)

    X_train, X_holdout, y_train, y_holdout, w_train, w_holdout = train_test_split(
        X, y, sample_weights,
        test_size=0.2,
        stratify=y,
        random_state=config.RANDOM_SEED,
    )

    print("Tuning XGBoost...")
    best_xgb = _tune_xgb(X_train, y_train, w_train, n_trials=8)
    print("Tuning LightGBM...")
    best_lgb = _tune_lgb(X_train, y_train, w_train, n_trials=8)

    if best_xgb["best_score"] >= best_lgb["best_score"]:
        base_model = xgb.XGBClassifier(
            objective="multi:softprob",
            num_class=len(np.unique(y)),
            random_state=config.RANDOM_SEED,
            eval_metric="mlogloss",
            tree_method="hist",
            **{k: v for k, v in best_xgb.items() if k != "best_score"},
        )
        base_model_name = "XGBoost"
        selected_params = {k: v for k, v in best_xgb.items() if k != "best_score"}
    else:
        base_model = lgb.LGBMClassifier(
            objective="multiclass",
            num_class=len(np.unique(y)),
            random_state=config.RANDOM_SEED,
            n_jobs=-1,
            **{k: v for k, v in best_lgb.items() if k != "best_score"},
        )
        base_model_name = "LightGBM"
        selected_params = {k: v for k, v in best_lgb.items() if k != "best_score"}

    X_core, X_calib, y_core, y_calib, w_core, w_calib = train_test_split(
        X_train, y_train, w_train,
        test_size=0.15,
        stratify=y_train,
        random_state=config.RANDOM_SEED,
    )

    fit_kwargs = {"sample_weight": w_core}
    if base_model_name == "LightGBM":
        fit_kwargs["callbacks"] = [lgb.early_stopping(25, verbose=False)]
    else:
        fit_kwargs["verbose"] = False
    base_model.fit(
        X_core, y_core,
        eval_set=[(X_calib, y_calib)],
        **fit_kwargs,
    )

    calibrated = CalibratedClassifierCV(
        estimator=FrozenEstimator(base_model),
        method="isotonic",
    )
    calibrated.fit(X_calib, y_calib)

    holdout_metrics = _evaluate_model(calibrated, X_holdout, y_holdout)

    # Generate reports (confusion matrix, reliability curve) for current model
    holdout_proba = calibrated.predict_proba(X_holdout)
    holdout_pred = holdout_proba.argmax(axis=1)
    class_names = label_encoder.classes_.tolist()
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    plot_confusion_matrix(
        y_holdout, holdout_pred,
        label_names=class_names,
        output_path=config.REPORTS_DIR / "confusion_matrix.png",
    )
    plot_reliability_curve(y_holdout, holdout_proba, config.REPORTS_DIR / "reliability_curve.png")
    print(f"Reports saved to {config.REPORTS_DIR}")

    joblib.dump(base_model, config.BASE_MODEL_PATH)
    joblib.dump(calibrated, config.CALIBRATED_MODEL_PATH)
    # Save calibrated model to main inference path (career_predictor.pkl)
    joblib.dump(calibrated, config.MODELS_DIR / "career_predictor.pkl")
    joblib.dump(label_encoder, config.LABEL_ENCODER_PATH)

    # Save feature manifest for inference (questionnaire_to_features needs to produce same columns)
    feature_manifest = {
        "feature_names": feature_cols,
        "model_type": "combined_tabular",
        "training_data": data_path.name,
    }
    write_json(feature_manifest, config.FEATURE_MANIFEST_PATH)

    summary = {
        "model_type": base_model_name,
        "timestamp": utc_timestamp(),
        "training_data": str(data_path),
        "num_features": len(feature_cols),
        "feature_names": feature_cols,
        "num_classes": len(label_encoder.classes_),
        "classes": label_encoder.classes_.tolist(),
        "holdout": holdout_metrics,
        "hyperparameters": selected_params,
    }
    write_json(summary, config.TRAINING_SUMMARY_PATH)

    print("\nTraining complete.")
    print(f"Holdout Top-1: {holdout_metrics['top1']:.3f}")
    print(f"Holdout Top-3: {holdout_metrics['top3']:.3f}")
    print(f"Holdout Macro F1: {holdout_metrics['macro_f1']:.3f}")
    print(f"Model saved to {config.BASE_MODEL_PATH}")


if __name__ == "__main__":
    main()
