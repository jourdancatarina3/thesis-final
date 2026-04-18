from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.calibration import calibration_curve
from sklearn.metrics import confusion_matrix


def plot_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    label_names: Sequence[str],
    output_path: Path,
) -> None:
    cm = confusion_matrix(y_true, y_pred, labels=range(len(label_names)))
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=label_names,
        yticklabels=label_names,
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix (Holdout Set)")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_reliability_curve(
    y_true: np.ndarray,
    proba: np.ndarray,
    output_path: Path,
) -> None:
    top1_pred = proba.argmax(axis=1)
    correct = (top1_pred == y_true).astype(int)
    confidences = proba.max(axis=1)

    frac_pos, mean_pred = calibration_curve(
        correct, confidences, n_bins=10, strategy="uniform"
    )

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
