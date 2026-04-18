#!/bin/bash
# Full pipeline: augment -> train -> validate
# Run from project root: ./scripts/run_full_pipeline.sh
# Uses .venv if it exists, otherwise system python3

set -e
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then PYTHON=python3; fi

echo "=== 1. Augmenting training data with gold profiles ==="
$PYTHON scripts/augment_training_data.py

echo ""
echo "=== 2. Training model ==="
$PYTHON scripts/train_combined_model.py

echo ""
echo "=== 3. Validating gold profiles ==="
$PYTHON scripts/validate_gold_profiles.py --relaxed
