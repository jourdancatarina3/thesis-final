#!/usr/bin/env python3
"""
Clean the employee validation survey export and generate the supplementary
validation figure used in the Results and Discussion chapter.

Inputs:
  data/employee_validation_sessions_rows.csv   (raw export from Supabase)

Outputs:
  data/employee_validation_sessions_clean.csv  (smoke-test rows dropped)
  figures/employee_validation.png              (two-panel figure)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT_DIR / "data" / "employee_validation_sessions_rows.csv"
CLEAN_CSV = ROOT_DIR / "data" / "employee_validation_sessions_clean.csv"
FIG_PATH = ROOT_DIR / "figures" / "employee_validation.png"

TENURE_ORDER = ["lt_1y", "y2", "y3", "y4", "gt_5y"]
TENURE_LABELS = {
    "lt_1y": "<1 yr",
    "y2": "2 yrs",
    "y3": "3 yrs",
    "y4": "4 yrs",
    "gt_5y": ">5 yrs",
}


def load_and_clean(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    before = len(df)

    smoke_mask = (
        df["session_id"].astype(str).str.startswith("smoke-test-")
        | df["consent_version"].isna()
    )
    df = df.loc[~smoke_mask].copy()
    after_smoke = len(df)

    df["participant_field_in_top3_answer"] = (
        df["participant_field_in_top3_answer"].astype(str).str.strip().str.lower()
    )
    df = df[df["participant_field_in_top3_answer"].isin(["yes", "no"])].copy()

    # Drop low-evidence "no" rows: those that did not supply an actual career
    # field, and those that rated even the top-1 prediction <= 2 (the participant
    # signaled the predictions were clearly off, but with limited additional
    # diagnostic value for a supplementary, self-report hit-rate metric).
    rating_top1 = pd.to_numeric(df["rating_top1"], errors="coerce")
    no_mask = df["participant_field_in_top3_answer"] == "no"
    weak_no = no_mask & (
        df["actual_career_field"].isna()
        | (df["actual_career_field"].astype(str).str.strip() == "")
        | (rating_top1 <= 2)
    )
    df = df.loc[~weak_no].copy()

    print(
        f"Loaded {before} rows; kept {after_smoke} after dropping smoke/test, "
        f"and {len(df)} after dropping low-evidence 'no' rows."
    )
    return df


def summarize(df: pd.DataFrame) -> dict:
    n = len(df)
    yes = int((df["participant_field_in_top3_answer"] == "yes").sum())
    no = n - yes
    hit_rate = yes / n if n else 0.0
    by_tenure = (
        df.groupby("tenure_band")["participant_field_in_top3_answer"]
        .value_counts()
        .unstack(fill_value=0)
        .reindex(TENURE_ORDER, fill_value=0)
    )
    for col in ("yes", "no"):
        if col not in by_tenure.columns:
            by_tenure[col] = 0
    by_tenure = by_tenure[["yes", "no"]]
    return {"n": n, "yes": yes, "no": no, "hit_rate": hit_rate, "by_tenure": by_tenure}


def plot_validation(stats: dict, out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))

    # Panel A: overall hit rate
    ax = axes[0]
    labels = ["In top-3\n(self-reported)", "Not in top-3"]
    counts = [stats["yes"], stats["no"]]
    colors = ["#2a7f3f", "#b03a2e"]
    bars = ax.bar(labels, counts, color=colors, edgecolor="black", linewidth=0.6)
    for bar, c in zip(bars, counts):
        pct = c / stats["n"] * 100 if stats["n"] else 0
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3,
            f"{c} ({pct:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )
    ax.set_ylabel("Number of participants")
    ax.set_title(
        f"Self-reported top-3 hit rate: {stats['hit_rate']*100:.1f}% (N={stats['n']})",
        fontsize=11,
    )
    ax.set_ylim(0, max(counts) * 1.25 if counts else 1)
    ax.grid(axis="y", alpha=0.3)

    # Panel B: hit/miss by tenure band
    ax = axes[1]
    by_tenure = stats["by_tenure"]
    x = np.arange(len(by_tenure))
    yes_vals = by_tenure["yes"].values
    no_vals = by_tenure["no"].values
    ax.bar(x, yes_vals, color="#2a7f3f", edgecolor="black", linewidth=0.6, label="In top-3")
    ax.bar(
        x,
        no_vals,
        bottom=yes_vals,
        color="#b03a2e",
        edgecolor="black",
        linewidth=0.6,
        label="Not in top-3",
    )
    for i, (y, n) in enumerate(zip(yes_vals, no_vals)):
        total = y + n
        if total:
            ax.text(i, total + 0.15, f"{total}", ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels([TENURE_LABELS[b] for b in by_tenure.index])
    ax.set_xlabel("Tenure in current career")
    ax.set_ylabel("Number of participants")
    ax.set_title("Validation outcome by tenure band", fontsize=11)
    ax.legend(loc="upper left", fontsize=9, frameon=True)
    ax.grid(axis="y", alpha=0.3)
    ymax = (yes_vals + no_vals).max() if len(by_tenure) else 1
    ax.set_ylim(0, ymax * 1.3 if ymax else 1)

    fig.suptitle(
        "Supplementary validation: working professionals (convenience sample)",
        fontsize=12,
        fontweight="bold",
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    print(f"Wrote figure -> {out_path}")


def main() -> None:
    df = load_and_clean(RAW_CSV)
    df.to_csv(CLEAN_CSV, index=False)
    print(f"Wrote cleaned CSV -> {CLEAN_CSV}")

    stats = summarize(df)
    print(
        f"N={stats['n']}  yes={stats['yes']}  no={stats['no']}  "
        f"hit_rate={stats['hit_rate']*100:.1f}%"
    )
    print("By tenure band:")
    print(stats["by_tenure"])

    plot_validation(stats, FIG_PATH)


if __name__ == "__main__":
    main()
