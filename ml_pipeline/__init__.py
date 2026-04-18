"""
Career recommendation pipeline: configuration, questionnaire handling,
questionnaire-to-feature mapping, training helpers, and evaluation plots.

The supported workflow is the combined-tabular model (merge career datasets,
optional augmentation, train XGBoost/LightGBM, infer via heuristic mapping).
"""

from . import config

__all__ = ["config"]
