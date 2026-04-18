# Figures for Manuscript

Place the following PNG files in this directory for inclusion in the thesis manuscript:

| Filename | Description |
|----------|-------------|
| `confusion_matrix.png` | 14×14 confusion matrix on holdout set |
| `precision_recall.png` | Per-class precision and recall bar chart |
| `roc_auc_multi.png` | Multi-class ROC curves (micro/macro) |
| `f1_score.png` | Per-class F1 score bar chart |
| `reliability_curve.png` | Calibration curve (top-1 confidence vs observed accuracy) |
| `tsne_embeddings.png` | t-SNE visualization of feature space by career category |

**To generate all figures:** Run from project root (with xgboost, scikit-learn, etc. installed):

```bash
python scripts/generate_results_figures.py
```

This produces PNGs in `models/reports/` and copies them to `figures/`. The manuscript expects these files in `figures/`.
