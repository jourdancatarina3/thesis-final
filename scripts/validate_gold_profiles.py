#!/usr/bin/env python3
"""
Validate that gold questionnaire profiles predict their expected careers.

Runs each gold profile through the trained model and checks:
- Top-1 MUST match expected career (strict)
- Top-3 MUST include expected career (relaxed)

Exit code: 0 if all pass, 1 if any fail.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml_pipeline import config


def load_gold_profiles() -> dict:
    path = config.DATA_DIR / "gold_profiles.json"
    if not path.exists():
        raise FileNotFoundError(f"Gold profiles not found: {path}")
    data = json.loads(path.read_text())
    return data["profiles"]


def validate(require_top1: bool = True) -> tuple[list[str], list[str]]:
    """
    Validate all gold profiles using the actual API predict path (same as the web app;
    post-hoc probability boosts apply only if APPLY_QUESTIONNAIRE_PROBABILITY_BOOST is True).
    Returns (passed_careers, failed_careers).
    """
    profiles = load_gold_profiles()
    passed = []
    failed = []

    # Use the real predict API (same as frontend)
    try:
        from api.predict import predict
    except ImportError:
        # When run from project root, api is importable
        import sys
        sys.path.insert(0, str(ROOT))
        from api.predict import predict

    for career, answers in profiles.items():
        if len(answers) != 30:
            failed.append(f"{career}: invalid profile length {len(answers)}")
            continue

        responses = [{"questionId": i + 1, "answerIndex": a} for i, a in enumerate(answers)]
        results = predict(responses)
        top3 = [r["career"] for r in results]
        top1 = top3[0] if top3 else None

        if require_top1:
            if top1 == career:
                passed.append(career)
            else:
                failed.append(f"{career}: predicted top1={top1} (expected {career}), top3={top3}")
        else:
            if career in top3:
                passed.append(career)
            else:
                failed.append(f"{career}: not in top3={top3} (expected {career})")

    return passed, failed


def main():
    require_top1 = "--strict" in sys.argv
    relaxed = "--relaxed" in sys.argv
    if relaxed:
        require_top1 = False

    try:
        passed, failed = validate(require_top1=require_top1)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    mode = "top-1" if require_top1 else "top-3"
    print(f"\n=== Gold Profile Validation ({mode} mode) ===\n")
    print(f"PASSED ({len(passed)}):")
    for c in passed:
        print(f"  ✓ {c}")
    if failed:
        print(f"\nFAILED ({len(failed)}):")
        for msg in failed:
            print(f"  ✗ {msg}")
        sys.exit(1)
    print("\nAll profiles passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
