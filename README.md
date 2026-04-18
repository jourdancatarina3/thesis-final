# A Tabular Machine Learning Prototype for Career Category Recommendations in Philippine Senior High School

**Questionnaire-to-feature mapping and holdout evaluation**

| | |
| --- | --- |
| **Author** | Jourdan Ken D. Catarina |
| **Program** | BS Computer Science IV |
| **Institution** | University of the Philippines Cebu |
| **Document** | Thesis manuscript: `manuscript.tex` (compiled entry: `main.tex` if used) |

This repository holds the **engineering artifact** for the thesis above: a web-based questionnaire, a heuristic mapping from answers into a **29-dimensional tabular feature schema**, a **multiclass gradient boosting** classifier (XGBoost or LightGBM) with **isotonic calibration**, and scripts for merging career corpora, training, and evaluation. Training uses **merged career-profile tabular data only**. The questionnaire is used for **inference and for separate data collection**, not as supervised training labels.

## Scope of evidence (read first)

Reported accuracy and calibration metrics are **internal validation only**: a stratified **80/20** train and holdout split on the **same merged corpus** used to fit the model (random seed **42**). They do **not** prove real-world predictive validity for Filipino Senior High School (SHS) students. Any deployment would need external validation (for example counselor-judged relevance, usefulness studies, and alignment with strands or courses). The manuscript states this explicitly in the abstract, disclaimer box, and threat-to-validity discussion.

## What the system does

1. **Questionnaire (30 items)**  
   Captures interests, values, work preferences, and related dimensions aligned with the thesis instrument (see `questionnaire_appendix.tex` and `data/questionnaire.json`).

2. **Questionnaire-to-feature mapping**  
   Rule-based conversion into the same feature space as the merged training tables (`ml_pipeline/questionnaire_to_features.py`).

3. **Ranked recommendations**  
   **Top-3** career **category** suggestions among **14** labels, with probability-style scores after calibration.

4. **Frontend**  
   Next.js app under `frontend/` (Tailwind CSS) for delivery and progress handling.

## Data and modeling (summary aligned with the manuscript)

- **Real tabular rows:** 31,400 from three sources, merged for training features and labels.  
- **Synthetic gold profiles:** 14,078 rows in the augmented build described in the thesis for questionnaire alignment (see `data/SYNTHETIC_DATA_NOTES.md` and scripts under `scripts/`).  
- **Modeling rows after per-class downsampling:** 27,050 (stratified split yields **21,640** train and **5,410** holdout).  
- **Holdout headline results (in manuscript):** about **99.8%** top-1 and **99.9%** top-3 accuracy; calibration error (ECE on max predicted probability, 10 uniform bins) about **0.0015**. Strong linear baselines are reported as well, reflecting a highly separable feature space in corpus.

For merge rules, paths, and column semantics, see `data/DATA_MERGE_README.md`.

## Repository layout

```
thesis-v0.3/
├── manuscript.tex              # Thesis manuscript source
├── questionnaire_appendix.tex  # Full questionnaire text (appendix)
├── main.tex                    # Root LaTeX driver if used for compilation
├── ml_pipeline/                # Features, training helpers, questionnaire mapping
├── scripts/
│   ├── merge_career_datasets.py
│   ├── train_combined_model.py # Primary: tabular combined data (no questionnaire labels)
│   ├── augment_training_data.py
│   ├── train_model.py          # Legacy / alternate path
│   └── ...
├── data/                       # CSV/XLSX, mappings, questionnaire JSON, merge docs
├── models/                     # Trained artifacts and reports (generated)
├── notebooks/                  # Optional Jupyter workflows and notebook requirements
├── api/predict.py              # Prediction entry used with the app
└── frontend/                   # Next.js UI and API route to Python predictor
```

## Setup

### Python

```bash
python -m venv venv
source venv/bin/activate          # Linux / macOS
# Windows: venv\Scripts\activate

pip install -r requirements.txt
# For notebooks or XLSX ingestion, also use:
pip install -r notebooks/requirements.txt
```

On macOS, if XGBoost fails to load OpenMP, install OpenMP (for example with Homebrew: `brew install libomp`).

### Train the combined tabular model (primary path)

```bash
python scripts/merge_career_datasets.py
python scripts/train_combined_model.py
```

Outputs go under `models/` (for example `career_predictor.pkl`, `label_encoder.pkl`, `model_metadata.json`). Augmentation or full pipeline steps may use additional scripts such as `scripts/augment_training_data.py` or `scripts/run_full_pipeline.sh` depending on your build.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. Ensure trained model files are present where `api/predict.py` and the Next.js API route expect them.

## Usage

1. Start the frontend (`npm run dev` in `frontend/`).  
2. Complete the **30** questionnaire items.  
3. Review **top-3** career category recommendations and scores.  
4. Treat output as **decision support** for exploration and discussion with counselors or guardians, not as a deterministic placement or diagnosis.

## The 14 career categories

The classifier targets **14** broad college fields or courses (wording may vary slightly in the UI):

1. Engineering (civil, mechanical, electrical, industrial, and related)  
2. Computer Science and Technology  
3. Business and Management  
4. Accounting and Finance  
5. Nursing and Allied Health  
6. Medicine (pre-med and related medical fields)  
7. Education and Teaching  
8. Psychology and Behavioral Science  
9. Communication and Media  
10. Law and Legal Studies  
11. Architecture and Built Environment  
12. Agriculture and Environmental Studies  
13. Natural Sciences  
14. Arts and Design  

## Technology stack

| Area | Stack |
| --- | --- |
| Tabular ML | XGBoost, LightGBM, scikit-learn, Optuna, pandas, numpy |
| Calibration / evaluation | Isotonic calibration, metrics and plots as in thesis pipeline |
| Web | Next.js (App Router), TypeScript, Tailwind CSS |
| Bridge | Python predictor invoked from the Next.js API route |

## Related files

- **`SETUP.md`**  
  Older step-by-step notes; some steps may reference legacy notebook flows. Prefer this README and `data/DATA_MERGE_README.md` for the combined model story.  
- **`figures/README.md`**  
  Notes on generated figures.  
- **`THESIS_DEFENSE_NOTES.md`**, **`IMPLEMENTATION_SUMMARY.md`**, **`MODEL_IMPROVEMENT_PLAN.md`**  
  Supporting notes from the project lifecycle.

## License and intent

Academic and thesis use. Not a medical, psychological, or licensing service. Counselors and school policy remain authoritative for guidance decisions.
