from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

from . import config


def load_questionnaire(path: Path | None = None) -> Dict:
    """Load questionnaire JSON."""
    q_path = path or config.QUESTIONNAIRE_PATH
    with q_path.open("r", encoding="utf-8") as fp:
        questionnaire = json.load(fp)
    return questionnaire


def get_question_columns(questionnaire: Dict) -> List[str]:
    return [f"Q{q['id']}" for q in questionnaire["questions"]]


def get_category_columns(questionnaire: Dict) -> Dict[str, List[str]]:
    mapping: Dict[str, List[str]] = {}
    for question in questionnaire["questions"]:
        col = f"Q{question['id']}"
        mapping.setdefault(question["category"], []).append(col)
    return mapping


def questionnaire_summary(questionnaire: Dict) -> Tuple[int, List[str]]:
    total = questionnaire.get("total_questions", len(questionnaire["questions"]))
    categories = sorted(
        {question["category"] for question in questionnaire["questions"]}
    )
    return total, categories


