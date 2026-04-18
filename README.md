# Career Prediction ML System

A machine learning system that predicts top 3 career recommendations for Filipino SHS students. The **model is trained on combined career datasets only** (no questionnaire data). The 30-question questionnaire is used for **data collection, evaluation, and inference mapping** (responses are converted into the same tabular feature space as the training data).

## Features

- **30-question questionnaire**: Behavioral, academic, values, work activities, and problem-solving items
- **Combined training data**: `career_dataset.csv`, optional `new_career_dataset.xlsx`, `new_career_dataset2.csv`, and `career_path_in_all_field.csv`, merged with label alignment via `job_to_category_mapping.json`
- **Top-3 recommendations**: Ranked college fields/courses with probabilities
- **Next.js frontend**: Questionnaire UI and results

## Project structure

```
thesis-v0.3/
├── scripts/
│   ├── merge_career_datasets.py    # Merge sources → combined_career_dataset.csv
│   ├── augment_training_data.py   # Optional: add gold-profile synthetic rows
│   ├── train_combined_model.py    # Train calibrated booster on tabular features
│   ├── run_full_pipeline.sh       # augment → train → validate_gold_profiles
│   ├── validate_gold_profiles.py
│   ├── generate_results_figures.py  # Thesis figures → models/reports + figures/
│   └── regenerate_reports.py       # Refresh CM + reliability from current model
├── data/
│   ├── questionnaire.json
│   ├── job_to_category_mapping.json
│   ├── combined_career_dataset.csv   # generated
│   ├── combined_career_dataset_augmented.csv  # optional (augment script)
│   ├── gold_profiles.json           # optional (for augmentation)
│   └── DATA_MERGE_README.md
├── ml_pipeline/                   # Shared Python modules
├── models/                        # Trained artifacts (see .gitignore)
├── api/predict.py                 # Inference (used by Next.js API route)
├── frontend/
├── figures/                       # PNGs referenced by manuscript.tex
└── manuscript.tex
```

## Setup

### Python

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`openpyxl` is included so `merge_career_datasets.py` can read `new_career_dataset.xlsx` when present.

### Train the combined model

```bash
python scripts/merge_career_datasets.py
python scripts/augment_training_data.py   # optional; improves class balance
python scripts/train_combined_model.py
```

Or run `./scripts/run_full_pipeline.sh` (uses `.venv/bin/python` if available, else `python3`).

- `merge_career_datasets.py` writes `data/combined_career_dataset.csv` and updates mapping files as configured in the script.
- `train_combined_model.py` prefers `combined_career_dataset_augmented.csv` when it exists; otherwise it trains on `combined_career_dataset.csv`. It writes `models/career_predictor.pkl`, `models/label_encoder.pkl`, `models/feature_manifest.json` (`model_type: combined_tabular`), and `models/model_metadata.json`.

**Questionnaire**: Not used for training. At inference, `ml_pipeline/questionnaire_to_features.py` maps answers into the merged feature columns. See [data/DATA_MERGE_README.md](data/DATA_MERGE_README.md) for dataset details.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The Next.js route `app/api/predict/route.ts` spawns `api/predict.py` at the repo root; ensure the virtualenv’s Python is used or `python3` can import the `ml_pipeline` package.

### Inference requirements

`api/predict.py` **requires** a trained combined model: `models/feature_manifest.json` must exist and declare `"model_type": "combined_tabular"`. If not, the API prints instructions and errors (no legacy fallback).

## Usage

1. Start the frontend: `cd frontend && npm run dev`
2. Complete the 30-question flow
3. View top-3 recommendations

## Target categories

The classifier uses **14** target college fields/courses (see `ml_pipeline/config.TARGET_CAREERS` and the questionnaire copy in the app).

## Stack

- **Python**: pandas, scikit-learn, XGBoost/LightGBM, Optuna, calibration
- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS

## Troubleshooting

- **Missing models**: Run merge + train steps above; confirm `models/feature_manifest.json` and `career_predictor.pkl` exist.
- **macOS / XGBoost**: You may need `brew install libomp` for OpenMP.
- **Predict script fails from Next.js**: Check Python path in `frontend/app/api/predict/route.ts` and working directory (project root).

## License

Thesis / research use.
