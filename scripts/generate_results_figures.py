#!/usr/bin/env python3
"""
Generate all figures for the Results and Discussion section of the thesis.

Produces:
1. confusion_matrix.png - Confusion matrix (holdout set)
2. precision_recall.png - Per-class precision and recall bar chart
3. roc_auc_multi.png - Multi-class ROC curves (one-vs-rest, micro/macro)
4. f1_score.png - Per-class F1 score bar chart
5. tsne_embeddings.png - t-SNE visualization of feature space by career category

Requires: trained model (career_predictor.pkl), label_encoder.pkl, unified training CSV (augmented if present).
Run train_combined_model.py first if needed.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.manifold import TSNE
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import label_binarize

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from ml_pipeline import config
from ml_pipeline.utils import read_json

# Inline plotting to avoid shap dependency from evaluation module
import seaborn as sns
from sklearn.calibration import calibration_curve


def plot_confusion_matrix(y_true, y_pred, label_names, output_path):
    cm = confusion_matrix(y_true, y_pred, labels=range(len(label_names)))
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=label_names, yticklabels=label_names, ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix (Holdout Set)")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_reliability_curve(y_true, proba, output_path):
    top1_pred = proba.argmax(axis=1)
    correct = (top1_pred == y_true).astype(int)
    confidences = proba.max(axis=1)
    frac_pos, mean_pred = calibration_curve(correct, confidences, n_bins=10, strategy="uniform")
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(mean_pred, frac_pos, marker="o", label="Model")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfectly Calibrated")
    ax.set_xlabel("Predicted Confidence")
    ax.set_ylabel("Observed Accuracy")
    ax.set_title("Reliability Curve (Top-1)")
    ax.legend()
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def _load_data_and_model():
    """Load combined data and trained model. Mirrors train_combined_model pipeline."""
    data_path = (
        config.AUGMENTED_DATA_PATH
        if config.AUGMENTED_DATA_PATH.exists()
        else config.COMBINED_DATA_PATH
    )
    if not data_path.exists():
        raise FileNotFoundError("No unified training dataset found (run merge, then optionally augment).")

    df = pd.read_csv(data_path)
    df = df[df["career"].isin(config.TARGET_CAREERS)].copy()

    # Same downsampling as train_combined_model
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

    encoder = joblib.load(config.LABEL_ENCODER_PATH)
    feature_cols = [c for c in df.columns if c not in ("career", "course_name")]
    X = df[feature_cols].to_numpy(dtype=np.float64)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    y = encoder.transform(df["career"])
    class_names = encoder.classes_.tolist()

    model = joblib.load(config.MODELS_DIR / "career_predictor.pkl")

    _, X_holdout, _, y_holdout = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=config.RANDOM_SEED
    )

    return X_holdout, y_holdout, model, encoder, class_names


def plot_precision_recall(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    label_names: list,
    output_path: Path,
) -> None:
    """Plot per-class precision and recall as grouped bar chart."""
    precision, recall, _, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=range(len(label_names)), zero_division=0
    )
    x = np.arange(len(label_names))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 8))
    bars1 = ax.bar(x - width / 2, precision, width, label="Precision", color="#6366F1", alpha=0.9)
    bars2 = ax.bar(x + width / 2, recall, width, label="Recall", color="#10B981", alpha=0.9)

    ax.set_ylabel("Score")
    ax.set_xlabel("Career Category")
    ax.set_title("Per-Class Precision and Recall (Holdout Set)")
    ax.set_xticks(x)
    ax.set_xticklabels(label_names, rotation=45, ha="right", fontsize=8)
    ax.legend()
    ax.set_ylim(0, 1.05)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_roc_auc_multi(
    y_true: np.ndarray,
    proba: np.ndarray,
    label_names: list,
    output_path: Path,
    n_classes: int,
) -> None:
    """Plot multi-class ROC curves (micro and macro average)."""
    y_bin = label_binarize(y_true, classes=range(n_classes))

    # Micro-average ROC
    fpr_micro, tpr_micro, _ = roc_curve(y_bin.ravel(), proba.ravel())
    roc_auc_micro = roc_auc_score(y_bin, proba, average="micro")

    # Macro-average ROC
    fpr = {}
    tpr = {}
    roc_auc = {}
    for i in range(n_classes):
        fpr[i], tpr[i], _ = roc_curve(y_bin[:, i], proba[:, i])
        roc_auc[i] = roc_auc_score(y_bin[:, i], proba[:, i])

    all_fpr = np.unique(np.concatenate([fpr[i] for i in range(n_classes)]))
    mean_tpr = np.zeros_like(all_fpr)
    for i in range(n_classes):
        mean_tpr += np.interp(all_fpr, fpr[i], tpr[i])
    mean_tpr /= n_classes
    roc_auc_macro = roc_auc_score(y_bin, proba, average="macro")

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot(fpr_micro, tpr_micro, color="#6366F1", lw=2, label=f"Micro-average ROC (AUC = {roc_auc_micro:.3f})")
    ax.plot(all_fpr, mean_tpr, color="#10B981", lw=2, label=f"Macro-average ROC (AUC = {roc_auc_macro:.3f})")
    ax.plot([0, 1], [0, 1], "k--", lw=1, label="Random")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("Multi-Class ROC Curves (One-vs-Rest)")
    ax.legend(loc="lower right")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_f1_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    label_names: list,
    output_path: Path,
) -> None:
    """Plot per-class F1 score bar chart."""
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=range(len(label_names)), zero_division=0
    )

    fig, ax = plt.subplots(figsize=(12, 8))
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(label_names)))
    bars = ax.barh(range(len(label_names)), f1, color=colors)

    ax.set_yticks(range(len(label_names)))
    ax.set_yticklabels(label_names, fontsize=9)
    ax.set_xlabel("F1 Score")
    ax.set_title("Per-Class F1 Score (Holdout Set)")
    ax.set_xlim(0, 1.05)
    ax.axvline(x=np.mean(f1), color="red", linestyle="--", alpha=0.7, label=f"Macro F1 = {np.mean(f1):.3f}")
    ax.legend()
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_tsne(
    X: np.ndarray,
    y: np.ndarray,
    label_names: list,
    output_path: Path,
    perplexity: int = 30,
    random_state: int = 42,
) -> None:
    """Plot t-SNE visualization of feature space colored by career category."""
    n_samples = min(3000, len(X))
    if len(X) > n_samples:
        rng = np.random.default_rng(random_state)
        idx = rng.choice(len(X), n_samples, replace=False)
        X_sub = X[idx]
        y_sub = y[idx]
    else:
        X_sub = X
        y_sub = y

    tsne = TSNE(n_components=2, perplexity=perplexity, random_state=random_state, max_iter=1000)
    X_tsne = tsne.fit_transform(X_sub)

    fig, ax = plt.subplots(figsize=(12, 10))
    scatter = ax.scatter(
        X_tsne[:, 0],
        X_tsne[:, 1],
        c=y_sub,
        cmap="tab20",
        alpha=0.6,
        s=25,
        edgecolors="white",
        linewidth=0.3,
    )
    ax.set_xlabel("t-SNE Dimension 1")
    ax.set_ylabel("t-SNE Dimension 2")
    ax.set_title("t-Distributed Stochastic Neighbor Embedding (t-SNE) of Career Feature Space")

    cbar = plt.colorbar(scatter, ax=ax, ticks=range(len(label_names)))
    cbar.ax.set_yticklabels(label_names, fontsize=7)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def main() -> None:
    print("Loading data and model...")
    X_holdout, y_holdout, model, encoder, class_names = _load_data_and_model()

    proba = model.predict_proba(X_holdout)
    preds = proba.argmax(axis=1)
    n_classes = len(class_names)

    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating confusion_matrix.png...")
    plot_confusion_matrix(
        y_holdout, preds,
        label_names=class_names,
        output_path=config.REPORTS_DIR / "confusion_matrix.png",
    )

    print("Generating reliability_curve.png...")
    plot_reliability_curve(y_holdout, proba, config.REPORTS_DIR / "reliability_curve.png")

    print("Generating precision_recall.png...")
    plot_precision_recall(
        y_holdout, preds,
        label_names=class_names,
        output_path=config.REPORTS_DIR / "precision_recall.png",
    )

    print("Generating roc_auc_multi.png...")
    plot_roc_auc_multi(
        y_holdout, proba,
        label_names=class_names,
        output_path=config.REPORTS_DIR / "roc_auc_multi.png",
        n_classes=n_classes,
    )

    print("Generating f1_score.png...")
    plot_f1_score(
        y_holdout, preds,
        label_names=class_names,
        output_path=config.REPORTS_DIR / "f1_score.png",
    )

    print("Generating tsne_embeddings.png...")
    plot_tsne(
        X_holdout, y_holdout,
        label_names=class_names,
        output_path=config.REPORTS_DIR / "tsne_embeddings.png",
    )

    summary_path = config.TRAINING_SUMMARY_PATH
    if summary_path.exists():
        summary = read_json(summary_path)
        print("\n--- Summary Metrics ---")
        print(f"Top-1: {summary['holdout'].get('top1', 'N/A')}")
        print(f"Top-3: {summary['holdout'].get('top3', 'N/A')}")
        print(f"Macro F1: {summary['holdout'].get('macro_f1', 'N/A')}")

    # Copy figures to figures/ for manuscript (if directory exists or create it)
    figures_dir = ROOT_DIR / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    for png in config.REPORTS_DIR.glob("*.png"):
        dest = figures_dir / png.name
        shutil.copy2(png, dest)
        print(f"Copied to {dest}")

    print("\nAll figures saved to:", config.REPORTS_DIR)
    print("Copies also in figures/ for manuscript inclusion.")
    for f in config.REPORTS_DIR.glob("*.png"):
        print(f"  - {f.name}")


if __name__ == "__main__":
    main()
