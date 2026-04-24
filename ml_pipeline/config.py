from __future__ import annotations

from pathlib import Path

# Root directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = MODELS_DIR / "reports"

# Source tabular datasets (inputs to scripts/merge_career_datasets.py)
SOURCE_ACADEMIC_IT_ROLES_CSV = DATA_DIR / "source_academic_percentages_it_suggested_roles.csv"
SOURCE_STEM_RIASEC_CSV = DATA_DIR / "source_stem_scores_riasec_career_labels.csv"
SOURCE_CAREER_TRAJECTORIES_CSV = DATA_DIR / "source_career_trajectories_multidisciplinary_fields.csv"
SOURCE_MULTIPLE_INTELLIGENCE_XLSX = DATA_DIR / "source_multiple_intelligence_job_professions.xlsx"

# Merged training datasets (merge / augment pipeline outputs)
DATASET_TRAINING_UNIFIED_BALANCED_CSV = DATA_DIR / "dataset_training_unified_balanced_imputed.csv"
DATASET_TRAINING_UNIFIED_AUGMENTED_CSV = DATA_DIR / "dataset_training_unified_balanced_augmented.csv"
DATASET_TRAINING_RAW_UNION_CSV = DATA_DIR / "dataset_training_raw_union_by_source.csv"

# Primary paths used by training, augmentation, and reporting
COMBINED_DATA_PATH = DATASET_TRAINING_UNIFIED_BALANCED_CSV
AUGMENTED_DATA_PATH = DATASET_TRAINING_UNIFIED_AUGMENTED_CSV

# Data assets
QUESTIONNAIRE_PATH = DATA_DIR / "questionnaire.json"
JOB_MAPPING_PATH = DATA_DIR / "job_to_category_mapping.json"

# Model artifacts (combined tabular pipeline)
FEATURE_MANIFEST_PATH = MODELS_DIR / "feature_manifest.json"
LABEL_ENCODER_PATH = MODELS_DIR / "label_encoder.pkl"
BASE_MODEL_PATH = MODELS_DIR / "career_predictor.pkl"
CALIBRATED_MODEL_PATH = MODELS_DIR / "career_predictor_calibrated.pkl"
TRAINING_SUMMARY_PATH = MODELS_DIR / "model_metadata.json"

# Training defaults
RANDOM_SEED = 42

# Target college fields/courses for the classifier
TARGET_CAREERS = [
    "Engineering",
    "Computer Science & Technology",
    "Business & Management",
    "Accounting & Finance",
    "Nursing & Allied Health",
    "Medicine (Pre-Med & Medical Fields)",
    "Education / Teaching",
    "Psychology & Behavioral Science",
    "Communication & Media",
    "Law & Legal Studies",
    "Architecture & Built Environment",
    "Agriculture & Environmental Studies",
    "Natural Sciences",
    "Arts & Design",
]


def ensure_directories() -> None:
    """Ensure expected directories exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


ensure_directories()
