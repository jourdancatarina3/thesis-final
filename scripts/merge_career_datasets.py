#!/usr/bin/env python3
"""
Merge source CSV/XLSX files (see ml_pipeline.config SOURCE_* paths) into training
datasets with consistent 14-category labels.

Outputs:
1. dataset_training_unified_balanced_imputed.csv — processed: imputation, balanced sampling, sorted by category
2. dataset_training_raw_union_by_source.csv — raw: no imputation, no balancing, sorted by category
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from ml_pipeline import config

# Map career_path_in_all_field "Field" values to our 15 TARGET_CAREERS
FIELD_TO_CATEGORY = {
    "Engineering": "Engineering",
    "Computer Science": "Computer Science & Technology",
    "Business": "Business & Management",
    "Marketing": "Business & Management",
    "Finance": "Accounting & Finance",
    "Education": "Education / Teaching",
    "Medicine": "Medicine (Pre-Med & Medical Fields)",
    "Biology": "Natural Sciences",
    "Chemistry": "Natural Sciences",
    "Physics": "Natural Sciences",
    "Psychology": "Psychology & Behavioral Science",
    "Law": "Law & Legal Studies",
    "Architecture": "Architecture & Built Environment",
    "Art": "Arts & Design",
    "Music": "Arts & Design",
}


def load_mapping() -> dict:
    """Load job-to-category mapping."""
    path = config.DATA_DIR / "job_to_category_mapping.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _derive_mi_columns(df: pd.DataFrame) -> None:
    """
    Derive Multiple Intelligences from RIASEC, academic, and skill features.
    Replaces constant 12.0 with meaningful variation so imputation has signal.
    Scale: 5-20 (Naturalist 0-20). Uses mean of available signals, fallback 12.0.
    """
    def _s(x: pd.Series, lo: float = 5, hi: float = 20) -> pd.Series:
        """Scale 0-10 series to lo-hi."""
        if x.isna().all():
            return pd.Series(float("nan"), index=df.index)
        return lo + (x / 10.0) * (hi - lo)

    def _s100(x: pd.Series, lo: float = 5, hi: float = 20) -> pd.Series:
        """Scale 0-100 series to lo-hi."""
        if x.isna().all():
            return pd.Series(float("nan"), index=df.index)
        return lo + (x / 100.0) * (hi - lo)

    def _s5(x: pd.Series, lo: float = 5, hi: float = 20) -> pd.Series:
        """Scale 0-5 series to lo-hi."""
        if x.isna().all():
            return pd.Series(float("nan"), index=df.index)
        return lo + (x / 5.0) * (hi - lo)

    def _mean_or_nan(*series_list: pd.Series) -> pd.Series:
        """Mean of non-NaN values per row; NaN if all NaN."""
        stack = pd.concat([s for s in series_list if s is not None and not s.isna().all()], axis=1)
        if stack.empty:
            return pd.Series(float("nan"), index=df.index)
        return stack.mean(axis=1)

    r = df["R_score"] if "R_score" in df.columns else None
    i = df["I_score"] if "I_score" in df.columns else None
    a = df["A_score"] if "A_score" in df.columns else None
    s = df["S_score"] if "S_score" in df.columns else None
    c = df["C_score"] if "C_score" in df.columns else None
    comm = df["Communication_Skill"] if "Communication_Skill" in df.columns else None
    acad_verb = df["Academic_Verbal"] if "Academic_Verbal" in df.columns else None
    acad_quant = df["Academic_Quantitative"] if "Academic_Quantitative" in df.columns else None
    logical_q = df["Logical_quotient_rating"] if "Logical_quotient_rating" in df.columns else None
    science = df["Science_Score"] if "Science_Score" in df.columns else None
    acad_tech = df["Academic_Technical"] if "Academic_Technical" in df.columns else None

    # Gardner's MI: derive from RIASEC + academic + skills (conceptual overlap)
    # Linguistic: language, communication
    l1 = _s(c) if c is not None else pd.Series(float("nan"), index=df.index)
    l2 = _s5(comm) if comm is not None else pd.Series(float("nan"), index=df.index)
    l3 = _s100(acad_verb) if acad_verb is not None else pd.Series(float("nan"), index=df.index)
    df["Linguistic"] = pd.concat([l1, l2, l3], axis=1).mean(axis=1, skipna=True).fillna(12.0).clip(5, 20)
    # Musical: arts -> A
    df["Musical"] = (_s(a) if a is not None else pd.Series(float("nan"), index=df.index)).fillna(12.0).clip(5, 20)
    # Bodily: hands-on -> R
    df["Bodily"] = (_s(r) if r is not None else pd.Series(float("nan"), index=df.index)).fillna(12.0).clip(5, 20)
    # Logical-Mathematical: logic, numbers -> I, Academic_Quantitative, Logical_quotient
    lm_parts = []
    if i is not None:
        lm_parts.append(_s(i))
    if acad_quant is not None:
        lm_parts.append(_s100(acad_quant))
    if logical_q is not None:
        lm_parts.append(_s(logical_q))
    df["Logical_Mathematical"] = (pd.concat(lm_parts, axis=1).mean(axis=1, skipna=True) if lm_parts else pd.Series(12.0, index=df.index)).fillna(12.0).clip(5, 20)
    # Spatial: visual, structural -> I + R, or Academic_Technical when RIASEC missing
    sp_parts = [s for s in [_s(i) if i is not None else None, _s(r) if r is not None else None] if s is not None]
    sp_tech = _s100(acad_tech) if acad_tech is not None else None
    if sp_parts:
        df["Spatial_Visualization"] = pd.concat(sp_parts + ([sp_tech] if sp_tech is not None else []), axis=1).mean(axis=1, skipna=True).fillna(12.0).clip(5, 20)
    elif sp_tech is not None:
        df["Spatial_Visualization"] = sp_tech.fillna(12.0).clip(5, 20)
    else:
        df["Spatial_Visualization"] = 12.0
    # Interpersonal: people -> S
    df["Interpersonal"] = (_s(s) if s is not None else pd.Series(float("nan"), index=df.index)).fillna(12.0).clip(5, 20)
    # Intrapersonal: self-reflection -> I
    df["Intrapersonal"] = (_s(i) if i is not None else pd.Series(float("nan"), index=df.index)).fillna(12.0).clip(5, 20)
    # Naturalist: nature, science
    nat_parts = []
    if i is not None:
        nat_parts.append(_s(i))
    if science is not None:
        nat_parts.append(_s100(science))
    df["Naturalist"] = (pd.concat(nat_parts, axis=1).mean(axis=1, skipna=True) if nat_parts else pd.Series(12.0, index=df.index)).fillna(12.0).clip(0, 20)


def _to_course_name(val) -> str:
    """Extract course/career name from source. Empty string if missing or invalid."""
    if pd.isna(val) or val is None:
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none", ""):
        return ""
    return s


def map_label_to_category(label: str, mapping: dict) -> str | None:
    """
    Map a job/career label to one of the target categories.
    Returns None if no match - caller should exclude those rows (don't force into a category).
    """
    if pd.isna(label) or not str(label).strip():
        return None

    label_str = str(label).strip()

    # Check explicit mappings first
    explicit = mapping.get("explicit_mappings", {})
    if label_str in explicit:
        return explicit[label_str]

    # Keyword-based matching (case-insensitive)
    label_lower = label_str.lower()
    keyword_rules = mapping.get("keyword_rules", {})

    for category, keywords in keyword_rules.items():
        for kw in keywords:
            if kw.lower() in label_lower:
                return category

    # No match - return None so caller excludes (don't force into default category)
    return None


def map_field_and_career_to_category(field: str, career: str, mapping: dict) -> str:
    """
    Map career_path_in_all_field (Field, Career) to one of 15 target categories.
    Uses Career (actual job name) as primary - e.g. Civil Engineer -> Engineering,
    Chemist -> Natural Sciences - since Field can be misleading (Finance + Civil Engineer).
    """
    return map_label_to_category(career, mapping)


def load_career_dataset() -> pd.DataFrame:
    """Load academic percentages / IT suggested roles source table."""
    df = pd.read_csv(config.SOURCE_ACADEMIC_IT_ROLES_CSV)
    # Drop unnamed index column if present
    if df.columns[0] == "Unnamed: 0" or df.columns[0].startswith("Unnamed"):
        df = df.drop(columns=[df.columns[0]], errors="ignore")
    df["_source"] = "career_dataset"
    df["_raw_label"] = df["Suggested Job Role"]
    return df


def load_new_career_dataset2() -> pd.DataFrame:
    """Load STEM / RIASEC scores with career label column."""
    df = pd.read_csv(config.SOURCE_STEM_RIASEC_CSV)
    df["_source"] = "new_career_dataset2"
    df["_raw_label"] = df["Career"]
    return df


def load_career_path_in_all_field() -> pd.DataFrame:
    """Load multidisciplinary career trajectory / field paths source table."""
    path = config.SOURCE_CAREER_TRAJECTORIES_CSV
    if not path.exists():
        raise FileNotFoundError(f"Career trajectories source CSV not found at {path}")
    df = pd.read_csv(path)
    df["_source"] = "career_path_in_all_field"
    return df


def prepare_career_path_in_all_field(
    df: pd.DataFrame, schema: dict, mapping: dict
) -> pd.DataFrame:
    """
    Prepare career_path_in_all_field for merge.
    Maps by Career (actual job name) to category - e.g. Civil Engineer -> Engineering,
    Chemist -> Natural Sciences. Field is ignored to avoid misclassification
    (e.g. Finance + Civil Engineer was wrongly -> Accounting & Finance).
    """
    df = df.copy()
    df["career"] = df.apply(
        lambda row: map_field_and_career_to_category(
            row["Field"], row["Career"], mapping
        ),
        axis=1,
    )
    df["course_name"] = df["Career"].apply(_to_course_name)  # From actual data only; empty if missing
    # Exclude rows that don't match any category (career is None)
    df = df[df["career"].notna()].copy()
    df = df[df["career"].isin(config.TARGET_CAREERS)]

    # Derive unified schema features from career_path columns
    # GPA (2.5-5) -> Math_Score, Science_Score (65-94)
    gpa = df["GPA"].fillna(3.5).clip(2.0, 5.0)
    df["Math_Score"] = 65 + (gpa - 2) * 9.67  # 2->65, 5->94
    df["Science_Score"] = df["Math_Score"]

    # Coding_Skills (0-4) -> Technical_Skill (2-5), Technical_Skill_Rating (1-9)
    coding = df["Coding_Skills"].fillna(2).clip(0, 4)
    df["Technical_Skill"] = 2 + coding * 0.75
    df["Technical_Skill_Rating"] = 1 + coding * 2

    # Communication_Skills, Presentation_Skills -> Communication_Skill, public_speaking
    comm = df["Communication_Skills"].fillna(2).clip(0, 4)
    pres = df["Presentation_Skills"].fillna(2).clip(0, 4)
    df["Communication_Skill"] = 2 + comm * 0.75
    df["public_speaking_points"] = 1 + (comm + pres) / 2 * 2

    # Problem_Solving, Analytical -> Logical_Ability, Logical_quotient_rating
    prob = df["Problem_Solving_Skills"].fillna(2).clip(0, 4)
    anal = df["Analytical_Skills"].fillna(2).clip(0, 4)
    df["Logical_Ability"] = 2 + (prob + anal) / 8 * 3
    df["Logical_quotient_rating"] = 1 + (prob + anal) / 2 * 2

    # Projects -> Projects_Count (general, not CS-specific)
    df["Projects_Count"] = df["Projects"].fillna(1).clip(0, 6)
    df["Hours_working_per_day"] = 8 + df["Internships"].fillna(0) / 2  # 8-10

    # General academic columns (not 9 CS-specific ones)
    base_pct = 60 + gpa * 4 + df["Field_Specific_Courses"].fillna(4) * 1.5
    base_pct = base_pct.clip(60, 94)
    df["Academic_Quantitative"] = base_pct
    df["Academic_Technical"] = base_pct
    df["Academic_Verbal"] = base_pct

    # RIASEC: derive from mapped career category (not Field) so features reflect
    # the actual career, e.g. a Chemist always gets science RIASEC regardless of
    # which Field row it appeared in.
    riasec_by_category = {
        "Engineering":                          (7, 6, 2, 3, 4, 4),
        "Computer Science & Technology":        (3, 8, 3, 2, 4, 5),
        "Natural Sciences":                     (5, 8, 2, 2, 2, 5),
        "Medicine (Pre-Med & Medical Fields)":  (3, 7, 2, 7, 2, 4),
        "Nursing & Allied Health":              (3, 6, 2, 8, 2, 4),
        "Education / Teaching":                 (2, 3, 4, 8, 3, 4),
        "Business & Management":               (2, 3, 2, 4, 8, 6),
        "Accounting & Finance":                 (2, 4, 2, 2, 5, 8),
        "Law & Legal Studies":                  (2, 4, 2, 4, 5, 7),
        "Architecture & Built Environment":     (5, 4, 6, 2, 4, 3),
        "Arts & Design":                        (2, 3, 9, 4, 2, 2),
        "Psychology & Behavioral Science":      (2, 5, 3, 8, 3, 4),
        "Communication & Media":               (2, 3, 5, 5, 5, 4),
        "Agriculture & Environmental Studies":  (7, 5, 2, 3, 3, 4),
    }
    default_riasec = (3, 4, 3, 4, 4, 4)
    riasec_cols = ["R_score", "I_score", "A_score", "S_score", "E_score", "C_score"]
    for i, col in enumerate(riasec_cols):
        df[col] = df["career"].apply(
            lambda c, idx=i: riasec_by_category.get(str(c).strip(), default_riasec)[idx]
        )

    # Metadata placeholders
    df["Sr.No."] = 36.5
    df["Course"] = 0.0
    _derive_mi_columns(df)

    # Ensure we have all unified schema columns
    all_cols = schema["all_numeric"]
    for c in all_cols:
        if c not in df.columns:
            df[c] = float("nan")
    out_cols = ["career", "course_name", "_source"] + all_cols
    return df[out_cols].copy()


def load_new_career_dataset_xlsx() -> pd.DataFrame | None:
    """Load multiple-intelligence / job profession XLSX if openpyxl is available."""
    xlsx = config.SOURCE_MULTIPLE_INTELLIGENCE_XLSX
    try:
        df = pd.read_excel(xlsx)
    except ImportError:
        print(f"Warning: openpyxl not installed. Skipping {xlsx.name}")
        print("  Install with: pip install openpyxl")
        return None
    except FileNotFoundError:
        print(f"Warning: {xlsx.name} not found. Skipping.")
        return None

    # Determine label column
    label_col = None
    for c in ["Job Profession", "Career", "job_profession", "career"]:
        if c in df.columns:
            label_col = c
            break
    if label_col is None:
        label_col = df.columns[-1]  # Assume last column is target

    df["_source"] = "new_career_dataset"
    df["_raw_label"] = df[label_col]
    return df


def build_unified_schema() -> dict:
    """
    Define the unified feature schema with GENERAL, category-neutral features.
    Replaces 9 CS-specific subject columns with 3 general academic columns to avoid
    bias toward Computer Science & Technology.
    """
    # Source column names (career_dataset) - used to derive general features
    career_source_cols = [
        "Acedamic percentage in Operating Systems",
        "percentage in Algorithms",
        "Percentage in Programming Concepts",
        "Percentage in Software Engineering",
        "Percentage in Computer Networks",
        "Percentage in Electronics Subjects",
        "Percentage in Computer Architecture",
        "Percentage in Mathematics",
        "Percentage in Communication skills",
        "Hours working per day",
        "Logical quotient rating",
        "hackathons",
        "coding skills rating",
        "public speaking points",
    ]

    # Output: general feature names (not CS-biased)
    # Academic_Quantitative (math/logic), Academic_Technical (one composite), Academic_Verbal
    # + Projects_Count (was hackathons), Technical_Skill_Rating, Technical_Skill (was Programming_Skill)
    general_numeric = [
        "Academic_Quantitative",
        "Academic_Technical",
        "Academic_Verbal",
        "Math_Score",
        "Science_Score",
        "Hours_working_per_day",
        "Logical_quotient_rating",
        "Projects_Count",
        "Technical_Skill_Rating",
        "public_speaking_points",
        "Communication_Skill",
        "Logical_Ability",
        "Technical_Skill",
        "R_score",
        "I_score",
        "A_score",
        "S_score",
        "E_score",
        "C_score",
        "Sr.No.",
        "Course",
        "Linguistic",
        "Musical",
        "Bodily",
        "Logical_Mathematical",
        "Spatial_Visualization",
        "Interpersonal",
        "Intrapersonal",
        "Naturalist",
    ]

    return {
        "career_source_cols": career_source_cols,
        "ds2_numeric": [
            "Math_Score",
            "Science_Score",
            "Technical_Skill",  # was Programming_Skill
            "Communication_Skill",
            "Logical_Ability",
            "R_score",
            "I_score",
            "A_score",
            "S_score",
            "E_score",
            "C_score",
        ],
        "all_numeric": general_numeric,
    }


def prepare_career_dataset(df: pd.DataFrame, mapping: dict, schema: dict) -> pd.DataFrame:
    """Prepare career_dataset for merge. Derive general (non-CS-biased) features."""
    df = df.copy()
    df["career"] = df["_raw_label"].apply(lambda x: map_label_to_category(x, mapping))
    df = df[df["career"].notna()].copy()  # Exclude rows that don't match any category
    df["course_name"] = df["_raw_label"].apply(_to_course_name)

    # Derive 3 general academic columns from the 9 CS-specific ones
    tech_cols = [
        "Acedamic percentage in Operating Systems",
        "Percentage in Programming Concepts",
        "Percentage in Software Engineering",
        "Percentage in Computer Networks",
        "Percentage in Electronics Subjects",
        "Percentage in Computer Architecture",
    ]
    tech_present = [c for c in tech_cols if c in df.columns]
    df["Academic_Quantitative"] = (
        (df["percentage in Algorithms"] + df["Percentage in Mathematics"]) / 2
        if "percentage in Algorithms" in df.columns and "Percentage in Mathematics" in df.columns
        else pd.Series(75.0, index=df.index)
    )
    df["Academic_Technical"] = (
        df[tech_present].mean(axis=1)
        if tech_present
        else pd.Series(75.0, index=df.index)
    )
    df["Academic_Verbal"] = (
        df["Percentage in Communication skills"]
        if "Percentage in Communication skills" in df.columns
        else pd.Series(75.0, index=df.index)
    )
    df["Math_Score"] = df["Percentage in Mathematics"] if "Percentage in Mathematics" in df.columns else float("nan")
    df["Science_Score"] = (
        (df["percentage in Algorithms"] + df["Percentage in Mathematics"]) / 2
        if "percentage in Algorithms" in df.columns and "Percentage in Mathematics" in df.columns
        else float("nan")
    )
    df["Hours_working_per_day"] = df["Hours working per day"] if "Hours working per day" in df.columns else float("nan")
    df["Logical_quotient_rating"] = df["Logical quotient rating"] if "Logical quotient rating" in df.columns else float("nan")
    df["Projects_Count"] = df["hackathons"] if "hackathons" in df.columns else float("nan")
    df["Technical_Skill_Rating"] = df["coding skills rating"] if "coding skills rating" in df.columns else float("nan")
    df["public_speaking_points"] = df["public speaking points"] if "public speaking points" in df.columns else float("nan")
    df["Communication_Skill"] = float("nan")
    df["Logical_Ability"] = float("nan")
    df["Technical_Skill"] = float("nan")
    df["R_score"] = df["I_score"] = df["A_score"] = df["S_score"] = df["E_score"] = df["C_score"] = float("nan")
    df["Sr.No."] = 36.5
    df["Course"] = 0.0
    _derive_mi_columns(df)

    out = df[["career", "course_name", "_source"] + schema["all_numeric"]].copy()
    return out


def prepare_new_career_dataset2(df: pd.DataFrame, mapping: dict, schema: dict) -> pd.DataFrame:
    """Prepare new_career_dataset2 for merge. Maps Programming_Skill -> Technical_Skill."""
    df = df.copy()
    df["career"] = df["_raw_label"].apply(lambda x: map_label_to_category(x, mapping))
    df = df[df["career"].notna()].copy()  # Exclude rows that don't match any category
    df["course_name"] = df["_raw_label"].apply(_to_course_name)

    df["Technical_Skill"] = df["Programming_Skill"] if "Programming_Skill" in df.columns else float("nan")
    _derive_mi_columns(df)
    out = df[["career", "course_name", "_source"]].copy()
    for c in schema["all_numeric"]:
        if c in df.columns:
            out[c] = df[c]
        else:
            out[c] = float("nan")
    return out


def prepare_new_career_dataset(
    df: pd.DataFrame, mapping: dict, schema: dict
) -> pd.DataFrame:
    """Prepare new_career_dataset.xlsx for merge."""
    df = df.copy()
    df["career"] = df["_raw_label"].apply(lambda x: map_label_to_category(x, mapping))
    df = df[df["career"].notna()].copy()  # Exclude rows that don't match any category
    df["course_name"] = df["_raw_label"].apply(_to_course_name)
    if "Programming_Skill" in df.columns and "Technical_Skill" not in df.columns:
        df["Technical_Skill"] = df["Programming_Skill"]

    out = df[["career", "course_name", "_source"]].copy()
    for c in schema["all_numeric"]:
        out[c] = df[c] if c in df.columns else float("nan")
    return out


def prepare_career_dataset_raw(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Prepare career_dataset for raw merge - keep original columns, add career only."""
    df = df.copy()
    df["career"] = df["_raw_label"].apply(lambda x: map_label_to_category(x, mapping))
    df = df[df["career"].notna()].copy()  # Exclude rows that don't match any category
    out_cols = ["career", "_source"] + [c for c in df.columns if c not in ["career", "_source", "_raw_label"]]
    return df[out_cols].copy()


def prepare_new_career_dataset2_raw(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Prepare new_career_dataset2 for raw merge - keep original columns, add career only."""
    df = df.copy()
    df["career"] = df["_raw_label"].apply(lambda x: map_label_to_category(x, mapping))
    df = df[df["career"].notna()].copy()  # Exclude rows that don't match any category
    out_cols = ["career", "_source"] + [c for c in df.columns if c not in ["career", "_source", "_raw_label", "Career"]]
    return df[out_cols].copy()


def prepare_career_path_raw(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Prepare career_path_in_all_field for raw merge - keep original columns, add career only."""
    df = df.copy()
    df["career"] = df.apply(
        lambda row: map_field_and_career_to_category(
            row["Field"], row["Career"], mapping
        ),
        axis=1,
    )
    df = df[df["career"].notna()].copy()  # Exclude rows that don't match any category
    df = df[df["career"].isin(config.TARGET_CAREERS)]
    df["_source"] = "career_path_in_all_field"
    cols = [c for c in df.columns if c not in ["career", "_source"]]
    return df[["career", "_source"] + cols].copy()


def prepare_new_career_dataset_raw(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Prepare new_career_dataset.xlsx for raw merge - keep original columns, add career only."""
    label_col = None
    for c in ["Job Profession", "Career", "job_profession", "career"]:
        if c in df.columns:
            label_col = c
            break
    if label_col is None:
        label_col = df.columns[-1]
    df = df.copy()
    df["_raw_label"] = df[label_col]
    df["career"] = df["_raw_label"].apply(lambda x: map_label_to_category(x, mapping))
    df = df[df["career"].notna()].copy()  # Exclude rows that don't match any category
    out_cols = ["career", "_source"] + [c for c in df.columns if c not in ["career", "_source", "_raw_label", label_col]]
    return df[out_cols].copy()


def merge_raw(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Merge dataframes without imputation or balancing. Sort by category."""
    combined = pd.concat(dfs, ignore_index=True, sort=False)
    combined = combined[combined["career"].isin(config.TARGET_CAREERS)]
    combined = combined.sort_values("career").reset_index(drop=True)
    return combined


# Valid value bounds for each feature (min, max). Used to clip MICE output.
# Stricter bounds to prevent very high/low imputed values.
FEATURE_BOUNDS = {
    "Academic_Quantitative": (0, 100),
    "Academic_Technical": (0, 100),
    "Academic_Verbal": (0, 100),
    "Math_Score": (0, 100),
    "Science_Score": (0, 100),
    "Hours_working_per_day": (4, 16),
    "Logical_quotient_rating": (0, 10),
    "Projects_Count": (0, 10),
    "Technical_Skill_Rating": (0, 10),
    "public_speaking_points": (0, 10),
    "Communication_Skill": (0, 5),
    "Logical_Ability": (0, 5),
    "Technical_Skill": (0, 5),
    "R_score": (0, 10),
    "I_score": (0, 10),
    "A_score": (0, 10),
    "S_score": (0, 10),
    "E_score": (0, 10),
    "C_score": (0, 10),
    "Sr.No.": (0, 100),
    "Course": (0, 1),
    "Linguistic": (0, 20),
    "Musical": (0, 20),
    "Bodily": (0, 20),
    "Logical_Mathematical": (0, 20),
    "Spatial_Visualization": (0, 20),
    "Interpersonal": (0, 20),
    "Intrapersonal": (0, 20),
    "Naturalist": (0, 20),
}


def _clip_imputed_values(combined: pd.DataFrame) -> None:
    """Clip imputed values to valid ranges to avoid extreme MICE artifacts."""
    for col, (lo, hi) in FEATURE_BOUNDS.items():
        if col in combined.columns and combined[col].dtype in ["float64", "int64"]:
            combined[col] = combined[col].clip(lower=lo, upper=hi)


def _impute_mice(combined: pd.DataFrame) -> pd.DataFrame:
    """
    Impute missing values using KNN (k-nearest neighbors).
    More robust than MICE for mixed/constant columns; avoids singular matrix issues.
    Clips output to valid ranges to avoid extreme values.
    """
    numeric_cols = [
        c for c in combined.columns
        if c not in ["career", "_source", "course_name"]
        and combined[c].dtype in ["float64", "int64"]
    ]
    if not numeric_cols:
        return combined

    X = combined[numeric_cols].copy().replace([np.inf, -np.inf], np.nan)

    # Columns that are entirely NaN: fallback to median (0 or column median)
    all_nan_cols = [c for c in numeric_cols if X[c].isna().all()]
    for col in all_nan_cols:
        combined[col] = 0.0
        numeric_cols = [c for c in numeric_cols if c not in all_nan_cols]
    if not numeric_cols:
        return combined

    X = combined[numeric_cols].copy().replace([np.inf, -np.inf], np.nan)
    imputer = KNNImputer(n_neighbors=5, weights="distance")
    X_imputed = imputer.fit_transform(X)
    combined[numeric_cols] = X_imputed

    _clip_imputed_values(combined)
    return combined


def merge_and_fill(dfs: list[pd.DataFrame], schema: dict) -> pd.DataFrame:
    """Merge all dataframes, fill missing values (MICE). No balancing - keep natural distribution."""
    combined = pd.concat(dfs, ignore_index=True)

    # Ensure we only keep rows with valid career in TARGET_CAREERS
    combined = combined[combined["career"].isin(config.TARGET_CAREERS)]

    # Impute missing numeric values using MICE
    combined = _impute_mice(combined)
    return combined


def main() -> None:
    mapping = load_mapping()
    schema = build_unified_schema()

    dfs = []

    # Load academic / IT roles source
    df1 = load_career_dataset()
    df1_prep = prepare_career_dataset(df1, mapping, schema)
    dfs.append(df1_prep)
    print(f"Loaded {config.SOURCE_ACADEMIC_IT_ROLES_CSV.name}: {len(df1_prep)} rows")

    # Load STEM + RIASEC source
    df2 = load_new_career_dataset2()
    df2_prep = prepare_new_career_dataset2(df2, mapping, schema)
    dfs.append(df2_prep)
    print(f"Loaded {config.SOURCE_STEM_RIASEC_CSV.name}: {len(df2_prep)} rows")

    # Load multiple-intelligence XLSX (optional)
    df3 = load_new_career_dataset_xlsx()
    if df3 is not None:
        df3_prep = prepare_new_career_dataset(df3, mapping, schema)
        dfs.append(df3_prep)
        print(f"Loaded {config.SOURCE_MULTIPLE_INTELLIGENCE_XLSX.name}: {len(df3_prep)} rows")

    # Load career trajectories by field
    df4 = load_career_path_in_all_field()
    df4_prep = prepare_career_path_in_all_field(df4, schema, mapping)
    dfs.append(df4_prep)
    print(f"Loaded {config.SOURCE_CAREER_TRAJECTORIES_CSV.name}: {len(df4_prep)} rows")

    # --- Processed combined dataset (imputation, balancing, sorted by category) ---
    combined = merge_and_fill(dfs, schema)
    output_cols = [c for c in combined.columns if c != "_source"]
    combined = combined[output_cols].sort_values(["career", "course_name"]).reset_index(drop=True)
    out_path = config.DATASET_TRAINING_UNIFIED_BALANCED_CSV
    combined.to_csv(out_path, index=False)
    print(f"\nSaved combined dataset to {out_path}")
    print(f"Total rows: {len(combined)}")
    print(f"Career distribution:\n{combined['career'].value_counts().to_string()}")

    # --- Raw combined dataset (no imputation, no balancing, sorted by category) ---
    dfs_raw = []
    dfs_raw.append(prepare_career_dataset_raw(df1, mapping))
    dfs_raw.append(prepare_new_career_dataset2_raw(df2, mapping))
    if df3 is not None:
        dfs_raw.append(prepare_new_career_dataset_raw(df3, mapping))
    dfs_raw.append(prepare_career_path_raw(df4, mapping))
    raw_combined = merge_raw(dfs_raw)
    raw_output_cols = [c for c in raw_combined.columns if c != "_source"]
    raw_combined = raw_combined[raw_output_cols]
    raw_path = config.DATASET_TRAINING_RAW_UNION_CSV
    raw_combined.to_csv(raw_path, index=False)
    print(f"\nSaved raw combined dataset to {raw_path}")
    print(f"Total rows: {len(raw_combined)}")
    print(f"Career distribution:\n{raw_combined['career'].value_counts().to_string()}")


if __name__ == "__main__":
    main()
