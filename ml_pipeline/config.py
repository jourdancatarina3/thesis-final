from __future__ import annotations

from pathlib import Path

# Root directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = MODELS_DIR / "reports"

# Data assets
QUESTIONNAIRE_PATH = DATA_DIR / "questionnaire.json"
COMBINED_DATA_PATH = DATA_DIR / "combined_career_dataset.csv"
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
