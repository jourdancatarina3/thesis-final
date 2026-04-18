#!/usr/bin/env python3
"""
Augment combined_career_dataset.csv with synthetic samples from gold questionnaire profiles.

This ensures the model sees feature vectors that match questionnaire responses,
fixing the gap where training data came from different sources (job listings, surveys)
and inference comes from questionnaire_to_features().

- Adds synthetic samples per career from gold profiles + small noise
- Oversamples underrepresented careers (Nursing, Medicine, Psychology, etc.) to rebalance
- Output: data/combined_career_dataset_augmented.csv
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml_pipeline import config
from ml_pipeline.questionnaire_to_features import questionnaire_to_features, get_feature_names


# Minimum samples per career after augmentation (undersampled careers get boosted)
MIN_SAMPLES_PER_CAREER = 1800
# Extra gold-derived samples to add per career for questionnaire alignment (even if already above min)
GOLD_DERIVED_PER_CAREER = 400
# Noise level (std) for synthetic samples - small variation so they stay in career region
NOISE_STD = 0.08


def load_gold_profiles() -> dict:
    """Load gold profiles from JSON."""
    path = config.DATA_DIR / "gold_profiles.json"
    if not path.exists():
        raise FileNotFoundError(f"Gold profiles not found: {path}")
    data = json.loads(path.read_text())
    return data["profiles"]


def generate_synthetic_from_profile(
    career: str,
    profile: list[int],
    n_samples: int,
    feature_names: list[str],
    noise_std: float = NOISE_STD,
    rng: np.random.Generator = None,
) -> pd.DataFrame:
    """Generate n_samples synthetic rows from questionnaire profile + noise."""
    if rng is None:
        rng = np.random.default_rng(config.RANDOM_SEED)

    base_features = questionnaire_to_features(profile)
    if len(base_features) != len(feature_names):
        raise ValueError(f"Feature length mismatch: {len(base_features)} vs {len(feature_names)}")

    # course_name: use career-derived placeholder
    course_name = career.replace(" ", "_").replace("&", "and")[:40]

    rows = []
    for i in range(n_samples):
        noise = rng.normal(0, noise_std, size=len(base_features))
        noisy = base_features * (1 + np.clip(noise, -0.5, 0.5))
        # Ensure Sr.No. and Course stay reasonable
        for j, name in enumerate(feature_names):
            if "Sr.No" in name:
                noisy[j] = 36.5
            elif name == "Course":
                noisy[j] = 0.0
        row = {"career": career, "course_name": f"{course_name}_syn_{i}"}
        for j, name in enumerate(feature_names):
            row[name] = float(noisy[j])
        rows.append(row)

    return pd.DataFrame(rows)


def main():
    if not config.COMBINED_DATA_PATH.exists():
        print("Error: combined_career_dataset.csv not found. Run merge_career_datasets.py first.")
        sys.exit(1)

    df = pd.read_csv(config.COMBINED_DATA_PATH)
    df = df[df["career"].isin(config.TARGET_CAREERS)].copy()

    counts = df["career"].value_counts()
    print("Current sample counts per career:")
    for career in config.TARGET_CAREERS:
        n = counts.get(career, 0)
        print(f"  {career}: {n}")

    try:
        profiles = load_gold_profiles()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    rng = np.random.default_rng(config.RANDOM_SEED)
    feature_cols = [c for c in df.columns if c not in ("career", "course_name")]

    synthetic_dfs = []
    for career in config.TARGET_CAREERS:
        profile = profiles.get(career)
        if not profile:
            print(f"  Warning: no gold profile for {career}, skipping augmentation")
            continue

        current_n = counts.get(career, 0)
        need = max(0, MIN_SAMPLES_PER_CAREER - current_n)
        to_add = max(need, GOLD_DERIVED_PER_CAREER)

        syn = generate_synthetic_from_profile(
            career, profile, to_add, feature_cols, NOISE_STD, rng
        )
        synthetic_dfs.append(syn)
        print(f"  Added {to_add} synthetic samples for {career}")

    synthetic = pd.concat(synthetic_dfs, ignore_index=True)
    combined = pd.concat([df, synthetic], ignore_index=True)

    # Apply same column order and bounds as original
    feature_cols = [c for c in df.columns if c not in ("career", "course_name")]
    for col in feature_cols:
        if col in combined.columns:
            lo, hi = 0, 100
            if "Score" in col or "Academic" in col:
                lo, hi = 0, 100
            elif "Hours" in col:
                lo, hi = 4, 16
            elif col in ("Logical_quotient_rating", "Technical_Skill_Rating", "public_speaking_points"):
                lo, hi = 0, 10
            elif col in ("Communication_Skill", "Logical_Ability", "Technical_Skill"):
                lo, hi = 0, 5
            elif "score" in col.lower() and "R_score" in col or "I_score" in col or "A_score" in col or "S_score" in col or "E_score" in col or "C_score" in col:
                lo, hi = 0, 10
            elif "Linguistic" in col or "Musical" in col or "Bodily" in col or "Logical_Mathematical" in col or "Spatial" in col or "Interpersonal" in col or "Intrapersonal" in col:
                hi = 20
            elif "Naturalist" in col:
                lo, hi = 0, 20
            combined[col] = combined[col].clip(lower=lo, upper=hi)

    out_path = config.DATA_DIR / "combined_career_dataset_augmented.csv"
    combined.to_csv(out_path, index=False)
    print(f"\nSaved augmented dataset to {out_path}")
    print(f"Total rows: {len(combined)} (was {len(df)})")

    # Final counts
    print("\nFinal sample counts per career:")
    for career in config.TARGET_CAREERS:
        n = (combined["career"] == career).sum()
        print(f"  {career}: {n}")


if __name__ == "__main__":
    main()
