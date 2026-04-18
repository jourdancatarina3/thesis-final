"""
Python API for career prediction using the combined tabular model.

Questionnaire responses are mapped to the merged dataset feature space via
`questionnaire_to_features` (heuristic). Training is survey-free; the
questionnaire is for collection, evaluation, and inference mapping only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from ml_pipeline.questionnaire_to_features import (
    get_feature_names,
    questionnaire_to_features,
    uses_combined_model,
)

MODELS_DIR = BASE_DIR / "models"

# When False, top-3 uses only calibrated probabilities (no questionnaire nudges).
APPLY_QUESTIONNAIRE_PROBABILITY_BOOST = False

_classifier_model = None
_label_encoder = None


def _require_combined_model() -> None:
    if uses_combined_model():
        return
    print(
        "Error: Combined tabular model is required.\n"
        "  1. python scripts/merge_career_datasets.py\n"
        "  2. python scripts/train_combined_model.py\n"
        "Training must write models/feature_manifest.json with "
        'model_type == "combined_tabular".',
        file=sys.stderr,
    )
    raise RuntimeError("Invalid or missing combined model manifest.")


def load_models() -> None:
    global _classifier_model, _label_encoder

    if _classifier_model is not None:
        return

    _require_combined_model()

    print("Loading models...", file=sys.stderr)
    _classifier_model = joblib.load(MODELS_DIR / "career_predictor.pkl")
    _label_encoder = joblib.load(MODELS_DIR / "label_encoder.pkl")
    print("Using combined (tabular) model.", file=sys.stderr)
    print("Models loaded successfully", file=sys.stderr)


def predict(responses):
    """
    Predict top 3 careers from questionnaire responses.

    Args:
        responses: List of dicts with 'questionId' and 'answerIndex'

    Returns:
        List of dicts with 'career', 'probability', 'traits'
    """
    global _classifier_model, _label_encoder

    load_models()

    sorted_responses = sorted(responses, key=lambda x: int(x["questionId"]))
    answer_indices = [resp["answerIndex"] for resp in sorted_responses]

    if len(answer_indices) != 30:
        raise ValueError(f"Expected 30 responses, got {len(answer_indices)}")

    features = questionnaire_to_features(answer_indices)
    col_names = get_feature_names()
    X = pd.DataFrame(features.reshape(1, -1), columns=col_names)

    probabilities = np.array(_classifier_model.predict_proba(X)[0], dtype=float)
    all_classes = _label_encoder.classes_

    if APPLY_QUESTIONNAIRE_PROBABILITY_BOOST:
        from ml_pipeline.questionnaire_to_features import (
            _agriculture_orientation_strength,
            _business_orientation_strength,
            _communication_orientation_strength,
            _education_orientation_strength,
            _law_orientation_strength,
            _medical_orientation_strength,
        )

        medical_strength = _medical_orientation_strength(answer_indices)
        education_strength = _education_orientation_strength(answer_indices)
        agriculture_strength = _agriculture_orientation_strength(answer_indices)
        communication_strength = _communication_orientation_strength(answer_indices)
        law_strength = _law_orientation_strength(answer_indices)
        business_strength = _business_orientation_strength(answer_indices)

        if medical_strength >= 0.5:
            med_label = "Medicine (Pre-Med & Medical Fields)"
            nurs_label = "Nursing & Allied Health"
            for i, c in enumerate(all_classes):
                if c == med_label or c == nurs_label:
                    boost = 0.50 + 0.08 * (medical_strength - 0.5)
                    probabilities[i] = min(1.0, probabilities[i] + boost)

        if business_strength >= 0.5 and business_strength > education_strength:
            biz_label = "Business & Management"
            ed_label = "Education / Teaching"
            for i, c in enumerate(all_classes):
                if c == biz_label:
                    boost = 0.80 + 0.12 * (business_strength - 0.5)
                    probabilities[i] = min(1.0, probabilities[i] + boost)
                elif c == ed_label and business_strength >= 0.6:
                    probabilities[i] = max(0, probabilities[i] - 0.22)

        if (
            education_strength >= 0.4
            and education_strength > medical_strength
            and education_strength > business_strength
        ):
            ed_label = "Education / Teaching"
            psych_label = "Psychology & Behavioral Science"
            for i, c in enumerate(all_classes):
                if c == ed_label:
                    boost = 0.80 + 0.12 * (education_strength - 0.4)
                    probabilities[i] = min(1.0, probabilities[i] + boost)
                elif c == psych_label and education_strength >= 0.6:
                    probabilities[i] = max(0, probabilities[i] - 0.35)

        if agriculture_strength >= 0.5 and agriculture_strength > education_strength:
            agr_label = "Agriculture & Environmental Studies"
            ed_label = "Education / Teaching"
            for i, c in enumerate(all_classes):
                if c == agr_label:
                    boost = 0.82 + 0.10 * (agriculture_strength - 0.5)
                    probabilities[i] = min(1.0, probabilities[i] + boost)
                elif c == ed_label and agriculture_strength >= 0.7:
                    probabilities[i] = max(0, probabilities[i] - 0.25)

        if communication_strength >= 0.6 and communication_strength > education_strength:
            comm_label = "Communication & Media"
            ed_label = "Education / Teaching"
            for i, c in enumerate(all_classes):
                if c == comm_label:
                    boost = 0.78 + 0.12 * (communication_strength - 0.6)
                    probabilities[i] = min(1.0, probabilities[i] + boost)
                elif c == ed_label and communication_strength >= 0.8:
                    probabilities[i] = max(0, probabilities[i] - 0.22)

        if law_strength >= 0.5 and law_strength > education_strength:
            law_label = "Law & Legal Studies"
            ed_label = "Education / Teaching"
            for i, c in enumerate(all_classes):
                if c == law_label:
                    boost = 0.80 + 0.12 * (law_strength - 0.5)
                    probabilities[i] = min(1.0, probabilities[i] + boost)
                elif c == ed_label and law_strength >= 0.6:
                    probabilities[i] = max(0, probabilities[i] - 0.20)

    top3_indices = np.argsort(probabilities)[-3:][::-1]

    results = []
    for idx in top3_indices:
        career = _label_encoder.inverse_transform([idx])[0]
        probability = float(probabilities[idx])
        results.append({"career": career, "probability": probability, "traits": []})

    return results


if __name__ == "__main__":
    input_data = json.load(sys.stdin)
    responses = input_data.get("responses", [])

    try:
        predictions = predict(responses)
        output = {"predictions": predictions}
        print(json.dumps(output))
    except Exception as e:
        error_output = {"error": str(e)}
        print(json.dumps(error_output), file=sys.stderr)
        sys.exit(1)
