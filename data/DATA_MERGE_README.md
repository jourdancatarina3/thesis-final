# Combined Career Dataset

This document describes the merged training dataset used for the career recommendation model.

## Data Sources

The combined dataset is built from three sources:

1. **career_dataset.csv** – Subject percentages (Operating Systems, Algorithms, Programming, etc.), skills, preferences, hours worked, logical quotient, coding skills, etc. Target: `Suggested Job Role` (9 IT-related roles).

2. **new_career_dataset.xlsx** – Multiple intelligences, P1–P8 dimensions. Target: `Job Profession`. (Included when openpyxl is installed.)

3. **new_career_dataset2.csv** – Math_Score, Science_Score, Programming_Skill, Communication_Skill, Logical_Ability, RIASEC scores (R/I/A/S/E/C). Target: `Career` (Accountant, Data Scientist, Doctor, Entrepreneur, Software Engineer, Teacher).

## Label Alignment

All raw job/career labels are mapped to the project’s **14 target college fields/courses** using:

- **job_to_category_mapping.json** – Rule-based mapping with explicit mappings and keyword rules
- **job_descriptions.csv** – Reference for job titles/roles when extending the mapping

Target categories: Engineering, Computer Science & Technology, Business & Management, Accounting & Finance, Nursing & Allied Health, Medicine (Pre-Med & Medical Fields), Education / Teaching, Psychology & Behavioral Science, Communication & Media, Law & Legal Studies, Architecture & Built Environment, Agriculture & Environmental Studies, Natural Sciences, Arts & Design.

## Merged Feature Set

| Feature Group | Source | Description |
|---------------|--------|-------------|
| Subject percentages | career_dataset | Operating Systems, Algorithms, Programming, Software Engineering, Computer Networks, Electronics, Computer Architecture, Mathematics, Communication skills |
| Work/skills | career_dataset | Hours per day, logical quotient, hackathons, coding skills rating, public speaking |
| Academic/skills | new_career_dataset2 | Math_Score, Science_Score, Programming_Skill, Communication_Skill, Logical_Ability |
| RIASEC | new_career_dataset2 | R_score, I_score, A_score, S_score, E_score, C_score |
| Multiple intelligences | new_career_dataset (if loaded) | P1–P8, other numeric columns |

## Why the Two Outputs Have Different Columns

| Output | Columns | Reason |
|--------|---------|--------|
| **combined_career_dataset.csv** | **37** (career + course_name + 35 features) | Uses a **unified schema**: every source is mapped into the same 35 feature names (e.g. `Acedamic_percentage_in_Operating_Systems`, `Math_Score`, `R_score`, `Linguistic`, …). Names are standardized (spaces → underscores). career_path rows are **transformed** (GPA → Math_Score, Field → RIASEC, etc.) so they match this schema. **course_name** holds the actual career/course (e.g. "Management Accounting", "Urban Planner") for display; the **career** column is the target category. |
| **raw_combined_career_dataset.csv** | **88** (union of all sources) | Keeps **each source’s original columns**. No renaming, no schema alignment. When dataframes are concatenated, the result has the **union** of every column: career_dataset’s columns (e.g. `Acedamic percentage in Operating Systems`, `Suggested Job Role`), new_career_dataset2’s (`Math_Score`, `R_score`, …), career_path’s (`Field`, `Career`, `GPA`, `Coding_Skills`, …). Rows from one source have NaN in the other sources’ columns. |

So: **combined** = one fixed feature set for modeling. **Raw** = all original columns preserved for inspection or other use.

## Missing Values (Processed Dataset Only)

- In the **processed** pipeline, rows from a source that lack a feature get `NaN` for that feature in the unified schema.
- Those missing values are then **imputed with MICE** in `scripts/merge_career_datasets.py` (see `_impute_mice` / `merge_and_fill`).

## Generating the Combined Datasets

```bash
# From project root
python scripts/merge_career_datasets.py
```

Outputs:
- **data/combined_career_dataset.csv** – Processed: missing values imputed with MICE in the merge script, balanced sampling (400 per category), sorted by category. Use for training.
- **data/raw_combined_career_dataset.csv** – Raw: no imputation (missing stays empty), no balancing, sorted by category. Union of all source columns; each row has values only for columns from its source.

## Questionnaire (Non-Training Use)

The 30-question questionnaire (`questionnaire.json`) is **not** used to train the main model. It is retained for:

- **Data collection** – Gathering responses from users
- **Evaluation** – Comparing system recommendations against questionnaire-based responses

The main production model is trained only on the combined non-survey datasets described above.
