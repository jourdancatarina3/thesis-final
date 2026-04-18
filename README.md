# A Tabular Machine Learning Prototype for Career Category Recommendations in Philippine Senior High School: Questionnaire-to-Feature Mapping and Holdout Evaluation

**Author:** Jourdan Ken D. Catarina (BS Computer Science IV, University of the Philippines Cebu)

This repository holds the implementation, dataset merge scripts, training pipeline, inference API, and Next.js questionnaire frontend for the thesis above.

## What the prototype does

- Collects answers through a **30-item** questionnaire (interests, values, work preferences, and related dimensions).
- Maps responses into a **29-dimensional** tabular feature schema via `ml_pipeline/questionnaire_to_features.py` so inference uses the same columns as the merged training corpora.
- Trains a **multiclass gradient boosting** classifier (XGBoost or LightGBM) with **isotonic post-hoc calibration**, then returns **ranked top-3** recommendations across **14 career categories** (college fields or courses).

Training uses **merged career-profile tabular data only**. The questionnaire is **not** used as supervised labels; it is for collection, evaluation framing, and inference mapping.

## Evidence scope (read this before citing metrics)

Reported accuracy and calibration numbers in the thesis write-up are **internal validation** on a **stratified 80/20** split of the merged tabular distribution (random seed **42**), after the modeling pipeline described there (including optional augmentation and per-class downsampling to **27,050** modeling rows in the reported configuration). They **do not** prove real-world predictive validity for Filipino SHS students. External validation (for example counselor-judged relevance or strand alignment) remains future work. For tables and discussion of limits on generalization, refer to the thesis document. Holdout metrics, baselines, and calibration plots appear in the evaluation chapter; you can regenerate related plots under `figures/` and `models/reports/` with the figure scripts in `scripts/`.

## Repository structure

```
thesis-v0.3/
├── scripts/
│   ├── merge_career_datasets.py     # Merge sources → combined_career_dataset.csv
│   ├── augment_training_data.py     # Optional synthetic rows (gold profiles)
│   ├── train_combined_model.py      # Train calibrated booster on tabular features
│   ├── run_full_pipeline.sh         # augment → train → validate_gold_profiles
│   ├── validate_gold_profiles.py
│   ├── generate_results_figures.py  # Figures → models/reports + figures/
│   └── regenerate_reports.py        # Refresh CM + reliability from current model
├── data/
│   ├── questionnaire.json
│   ├── job_to_category_mapping.json
│   ├── combined_career_dataset.csv           # generated
│   ├── combined_career_dataset_augmented.csv # optional
│   ├── gold_profiles.json                    # optional (augmentation)
│   └── DATA_MERGE_README.md
├── ml_pipeline/                   # Shared Python modules
├── models/                        # Trained artifacts (often gitignored)
├── api/predict.py                 # Inference (called from Next.js API route)
├── frontend/
└── figures/                       # PNGs (e.g. from generate_results_figures.py)
```

## Setup

### Python

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`openpyxl` is listed so `merge_career_datasets.py` can read `new_career_dataset.xlsx` when present.

### Train the combined model

```bash
python scripts/merge_career_datasets.py
python scripts/augment_training_data.py   # optional; class balance / alignment
python scripts/train_combined_model.py
```

Or run `./scripts/run_full_pipeline.sh` (uses `.venv/bin/python` if available, otherwise `python3`).

- Merge writes `data/combined_career_dataset.csv` (and updates mapping behavior as configured in the script).
- Training prefers `combined_career_dataset_augmented.csv` when it exists; otherwise `combined_career_dataset.csv`. Outputs include `models/career_predictor.pkl`, `models/label_encoder.pkl`, `models/feature_manifest.json` (`model_type: combined_tabular`), and `models/model_metadata.json`.

Dataset provenance and column rules: [data/DATA_MERGE_README.md](data/DATA_MERGE_README.md).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The App Router handler `frontend/app/api/predict/route.ts` runs `api/predict.py` from the repo root; Python must resolve the `ml_pipeline` package (virtualenv or `PYTHONPATH` as you prefer).

### Inference requirements

`api/predict.py` expects a trained combined model: `models/feature_manifest.json` with `"model_type": "combined_tabular"`. There is no legacy fallback if artifacts are missing.

## Usage

1. `cd frontend && npm run dev`
2. Complete the questionnaire flow.
3. Inspect top-3 career categories and scores.

## Labels and configuration

The **14** target categories are defined in `ml_pipeline/config.TARGET_CAREERS` and mirrored in the app copy. Questionnaire text lives in `data/questionnaire.json`.

## Stack

- **Python:** pandas, scikit-learn, XGBoost/LightGBM, Optuna, probability calibration
- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS

## Troubleshooting

- **Missing models:** Run merge and train; confirm `models/feature_manifest.json` and `models/career_predictor.pkl` exist.
- **macOS / XGBoost:** You may need `brew install libomp` for OpenMP.
- **Predict fails from Next.js:** Check the Python executable and working directory in `frontend/app/api/predict/route.ts` (project root).

## License

Thesis and research use.
