"""
Map 30-question questionnaire responses to the merged feature space.

The main model is trained on combined career datasets (tabular features only).
At inference, questionnaire responses are converted to this feature space via
heuristic mapping. The questionnaire is retained for data collection and
evaluation; it is NOT used for training.

Mapping is heuristic/rule-based. Questionnaire items conceptually overlap with:
- Academic interests (Q8-Q13) -> subject percentages, Math/Science scores
- Values and work activities -> RIASEC scores
- Behavioral items -> skills, logical ability, communication
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Sequence

import numpy as np

from . import config
from .utils import read_json


def _normalize_option(idx: int, num_options: int = 5) -> float:
    """Map option index 0..4 to 0..1."""
    return idx / max(num_options - 1, 1)


def _scale(val: float, lo: float, hi: float) -> float:
    """Scale value from [0,1] to [lo, hi]."""
    return lo + val * (hi - lo)


def _medical_orientation_strength(r: list) -> float:
    """
    Detect strength of medical/healthcare orientation from questionnaire.
    Key indicators: Q2 help recover, Q10 human body, Q15/Q16/Q17/Q18 helping,
    Q19 caring for patients, Q20 medical equipment, Q22 patient improves, Q25 recovery.
    Returns 0-1.
    """
    medical_signals = [
        r[1] == 3,   # Q2: help someone recover from illness
        r[9] == 0,   # Q10: human body and health systems
        r[14] == 0,  # Q15: patient or student improvement
        r[15] == 0,  # Q16: working with people in need
        r[16] == 0,  # Q17: lives I've helped improve
        r[17] == 0,  # Q18: opportunities to help others
        r[18] == 3,  # Q19: caring for patients
        r[19] == 3,  # Q20: medical equipment and patient care
        r[21] == 3,  # Q22: patient's condition improves
        r[24] == 3,  # Q25: assist in recovery or treatment
    ]
    return sum(medical_signals) / len(medical_signals)


def _agriculture_orientation_strength(r: list) -> float:
    """
    Detect strength of agriculture/environmental orientation from questionnaire.
    Key indicators: hands-on (Q7, Q21), practical (Q8), science (Q13), impact/purpose (Q14, Q18),
    research (Q9), nature/life (Q10=0) or systems (Q10=2), operate equipment (Q27).
    Exclude when clearly teaching-focused (education) or medical.
    Returns 0-1.
    """
    if r[18] == 3 or r[19] == 3:  # medical
        return 0.0
    if r[18] == 1 and r[19] == 1 and r[21] == 0 and r[9] == 4:
        # Strong teaching: Q19 teaching, Q20 learning, Q22 student, Q10 people learn
        if r[1] == 0 or r[24] == 1:  # Q2 see understand or Q25 guidance
            return 0.0  # likely Education, not Agriculture
    agriculture_signals = [
        r[6] == 0,   # Q7: working with hands
        r[7] == 4,   # Q8: practical application
        r[9] in (0, 2),  # Q10: life/nature OR structures/systems (env, agriculture)
        r[12] == 2,  # Q13: science
        r[13] == 4 or r[17] == 4,  # Q14 impact or Q18 greater purpose
        r[8] == 2,   # Q9: research
        r[20] == 0,  # Q21: fixing/building with hands
        r[26] == 3,  # Q27: operate equipment (farm, lab)
        r[15] == 1 or r[16] == 1,  # Q16 build solutions or Q17 innovations
    ]
    return sum(agriculture_signals) / len(agriculture_signals)


def _communication_orientation_strength(r: list) -> float:
    """
    Detect strength of communication/media orientation from questionnaire.
    Key indicators: visualizations (Q3), presenting (Q9, Q11, Q21), communication (Q7, Q12, Q13, Q23),
    people/customers (Q4, Q20, Q24), creative (Q15, Q26), business (Q10=3, Q27=4).
    Distinguishable from Education: Q10=3 (business) or Q15=2 (creative) or Q27=4 (strategic).
    Returns 0-1.
    """
    if r[18] == 3 or r[19] == 3:  # medical
        return 0.0
    # Strong Communication/Media signals (presenting, viz, language, business)
    comm_signals = [
        r[2] == 1,   # Q3: create visualizations (media content)
        r[3] == 0,   # Q4: interacting with people
        r[6] == 2,   # Q7: face-to-face communication
        r[8] == 4,   # Q9: present ideas to audience
        r[9] in (3, 4),  # Q10: business OR people (corporate comm, PR)
        r[10] == 2,  # Q11: the presenter
        r[11] == 3,  # Q12: social interaction and communication
        r[12] == 1,  # Q13: language and communication
        r[14] == 2,  # Q15: creative work appreciated (media/design)
        r[18] == 1,  # Q19: teaching/explaining (training, presenting)
        r[19] == 1,  # Q20: people and learning
        r[20] == 2,  # Q21: preparing and delivering presentation
        r[22] == 1,  # Q23: communicate clearly
        r[23] == 2,  # Q24: interact with customers
        r[25] == 1,  # Q26: be creative
        r[26] == 4,  # Q27: plan and execute business strategies (strategic comm)
    ]
    return sum(comm_signals) / len(comm_signals)


def _law_orientation_strength(r: list) -> float:
    """
    Detect strength of law/legal orientation from questionnaire.
    Key indicators: procedures (Q5), compliance/accuracy (Q16, Q26), frameworks (Q29),
    gather info (Q28), research (Q9), review/verify (Q21), business (Q10), language (Q13),
    precision (Q26), analyze (Q7=3).
    Exclude medical.
    Returns 0-1.
    """
    if r[18] == 3 or r[19] == 3:  # medical
        return 0.0
    law_signals = [
        r[4] == 0,   # Q5: clear procedures and protocols (legal procedures)
        r[15] == 3,  # Q16: ensuring accuracy and compliance (STRONG law signal)
        r[25] == 0,  # Q26: work with precision and accuracy (legal precision)
        r[28] == 3,  # Q29: apply established frameworks (legal frameworks)
        r[27] == 0,  # Q28: gathering all relevant information (legal research)
        r[8] in (2, 3),  # Q9: research OR collaborative (legal research, case work)
        r[9] == 3,   # Q10: how businesses operate (corporate law)
        r[12] == 1,  # Q13: language and communication (legal writing)
        r[20] in (2, 3),  # Q21: presenting (court) OR reviewing/verifying (legal review)
        r[23] in (2, 3),  # Q24: client interaction OR follow procedures precisely
        r[6] in (2, 3),  # Q7: face-to-face (client) OR analyzing (legal analysis)
    ]
    return sum(law_signals) / len(law_signals)


def _business_orientation_strength(r: list) -> float:
    """
    Detect strength of business/management orientation from questionnaire.
    Key indicators: Q10 businesses, Q14/Q15/Q18 financial, Q16/Q17 managing teams,
    Q19 financial analysis (not teaching), Q20 numbers/financial (not people/learning),
    Q24 manage projects, Q26 lead/coordinate, Q27 business strategies.
    Must be distinguishable from Education: Q10=3 (business) vs Q10=4 (people learn).
    Returns 0-1.
    """
    if r[18] == 3 or r[19] == 3:  # medical
        return 0.0
    business_signals = [
        r[3] == 3,   # Q4: managing and coordinating multiple activities
        r[5] == 2,   # Q6: leading a team or managing a project
        r[6] == 4,   # Q7: planning and organizing activities
        r[9] == 3,   # Q10: how businesses and organizations operate (STRONG)
        r[10] == 0,  # Q11: the organizer who keeps everyone on track
        r[13] == 3,  # Q14: achieving financial success and stability
        r[14] == 3,  # Q15: achieve a financial or business goal
        r[15] == 2,  # Q16: managing and leading teams
        r[16] == 2,  # Q17: the teams I've built and led
        r[17] == 3,  # Q18: offers financial security
        r[18] == 2,  # Q19: analyzing financial records (not teaching)
        r[19] == 2,  # Q20: numbers, spreadsheets, financial data (not people/learning)
        r[20] == 4,  # Q21: creating a plan or strategy
        r[23] == 0,  # Q24: manage multiple projects and deadlines
        r[25] == 4,  # Q26: lead and coordinate activities
        r[26] == 4,  # Q27: plan and execute business strategies
    ]
    return sum(business_signals) / len(business_signals)


def _education_orientation_strength(r: list) -> float:
    """
    Detect strength of teaching/education orientation from questionnaire.
    Key indicators: Q2 see understand, Q9 present, Q10 people learn, Q19 teaching,
    Q20 people/learning, Q22 student understands, Q25 guidance success.
    Must NOT be medical (Q19=3 caring patients, Q20=3 medical equipment) - teaching vs nursing.
    Returns 0-1.
    """
    # Teaching-specific: not medical (exclude caring for patients, medical equipment)
    if r[18] == 3 or r[19] == 3:  # caring patients or medical equipment → not education
        return 0.0
    education_signals = [
        r[1] == 0,   # Q2: see someone understand (teaching moment)
        r[8] == 4,   # Q9: present ideas to audience
        r[9] == 4,   # Q10: how people learn and develop
        r[18] == 1,  # Q19: teaching and explaining concepts
        r[19] == 1,  # Q20: people and their learning needs
        r[21] == 0,  # Q22: student finally understands (teaching moment)
        r[24] == 1,  # Q25: see someone succeed because of my guidance
    ]
    return sum(education_signals) / len(education_signals)


def questionnaire_to_features(responses: Sequence[int]) -> np.ndarray:
    """
    Convert 30 questionnaire response indices to the merged feature vector.

    Args:
        responses: List of 30 integers (0-4), one per question, in order Q1..Q30.

    Returns:
        1D numpy array of shape (n_features,) matching the combined dataset schema.
    """
    if len(responses) != 30:
        raise ValueError(f"Expected 30 responses, got {len(responses)}")

    r = list(responses)
    norm = lambda i: _normalize_option(r[i] if i < len(r) else 0)
    medical = _medical_orientation_strength(r)

    # --- General academic strengths (category-neutral, not CS-specific) ---
    # Q8: memorization(0), logical(1), creative(2), human behavior(3), practical(4)
    # Q10: human body(0), technology(1), structures(2), business(3), people(4)
    # Q13: math(0), language(1), science(2), social(3), arts(4)
    # CRITICAL: Q10 option 0 = human body/health -> life science, NOT low tech.
    # Medicine needs high science and naturalist. Treat human body as life-science strength.
    life_science = 0.9 if r[9] == 0 else 0.0  # Q10 human body
    tech_strength = (
        (life_science + norm(12)) / 2 if r[9] == 0 else (norm(9) + norm(12)) / 2
    )  # when human body, use life_science instead of norm(9)
    math_strength = (norm(7) + norm(12)) / 2   # Q8 logical, Q13 math
    comm_strength = norm(10)                   # Q11 presenter -> communication

    # 3 general academic columns (replaces 9 CS-specific subject percentages)
    academic_quantitative = _scale(math_strength, 60, 95)  # math, logic, analysis
    academic_technical = _scale(tech_strength, 60, 95)    # technical, science, life science
    academic_verbal = _scale(comm_strength, 60, 95)       # language, communication

    # --- Hours, logical quotient, projects, technical skill rating, public speaking ---
    hours = _scale((1 - norm(4)) * 0.5 + 0.5, 6, 11)  # 6-11
    logical_quotient = _scale(
        min(1.0, (norm(2) + norm(7) + norm(27) + norm(28)) / 4 + (0.25 if medical > 0.4 else 0)), 1, 9
    )  # Q3 numbers, Q8 logical, Q28 gather info, Q29 methodical; medical boost
    projects_count_raw = norm(8) + norm(18) / 2
    if medical > 0.5:
        projects_count_raw *= 0.55  # medical roles have fewer "projects" in CS sense
    projects_count = _scale(projects_count_raw, 0, 6)
    technical_skill_rating = _scale((norm(0) + norm(18) + norm(19)) / 3, 1, 9)
    public_speaking = _scale((norm(2) + norm(10) + norm(20)) / 3, 1, 9)

    # --- Math_Score, Science_Score (60-97) ---
    math_score = _scale(math_strength, 65, 97)
    science_base = (math_strength + tech_strength) / 2
    if r[9] == 0:  # human body -> boost science (life sciences)
        science_base = max(science_base, 0.75)
    science_score = _scale(science_base, 65, 97)

    # --- Technical_Skill, Communication_Skill, Logical_Ability (1-5) ---
    technical_skill = _scale(tech_strength, 2, 5)
    comm_skill = _scale(comm_strength, 2, 5)
    logical_ability = _scale((norm(2) + norm(7) + norm(11)) / 3, 2, 5)

    # --- RIASEC: R=Realistic, I=Investigative, A=Artistic, S=Social, E=Enterprising, C=Conventional ---
    r_base = (norm(6) + (1 - norm(20)) + norm(26)) / 3
    if medical > 0.5:
        r_base *= 0.6  # medicine in training data has lower R; temper hands-on signal
    r_score = _scale(r_base, 0, 9)
    # Fix I_score: was (1-norm(6))+norm(6)=0.5 always. Use Q1 diagnostic, Q3 stats, Q7 analyze, + medical boost.
    i_base = (norm(0) + norm(2) + norm(6)) / 3
    if medical > 0.3:
        i_base = min(1.0, i_base + 0.35)  # diagnostic, life-science = investigative
    i_score = _scale(i_base, 0, 9)
    a_score = _scale((norm(1) + norm(6) + norm(14) + norm(17)) / 4, 0, 9)
    s_score = _scale((norm(1) + norm(3) + norm(10) + norm(13)) / 4, 0, 9)
    e_score = _scale((norm(3) + norm(5) + norm(15) + norm(25)) / 4, 0, 9)
    c_score = _scale((norm(2) + (1 - norm(4)) + norm(15)) / 3, 0, 9)

    # --- Multiple intelligences (5-20 scale except Naturalist 0-20) ---
    # Naturalist = life sciences, biology, nature. Q10 human body(0) must boost strongly.
    naturalist_raw = (norm(9) + norm(12) + norm(13)) / 3
    if r[9] == 0:  # human body -> high naturalist (life science)
        naturalist_raw = max(naturalist_raw, 0.8)
    naturalist = _scale(naturalist_raw, 0, 20)
    linguistic = _scale((norm(10) + (1.0 if r[12] == 1 else 0.5) + norm(22)) / 3, 5, 20)
    musical = _scale((norm(1) + norm(6) + (1.0 if r[12] == 4 else 0.5)) / 3, 5, 20)
    bodily = _scale(((1.0 if r[6] == 0 else 0.5) + (1.0 if r[20] == 0 else 0.5) + norm(7)) / 3, 5, 20)
    logical_mathematical = _scale((norm(2) + norm(7) + norm(11) + (1.0 if r[12] == 0 else 0.5)) / 4, 5, 20)
    spatial_visualization = _scale((norm(2) + norm(9) + norm(18)) / 3, 5, 20)
    interpersonal = _scale((norm(1) + norm(3) + norm(10) + norm(13)) / 4, 5, 20)
    intrapersonal = _scale(((1.0 if r[3] == 1 else 0.5) + (1.0 if r[23] == 1 else 0.5)) / 2, 5, 20)
    sr_no = 36.5  # median placeholder (model was trained with these)
    course = 0.0   # metadata placeholder

    # Order must match merged combined_career_dataset schema (general_numeric)
    features = [
        academic_quantitative, academic_technical, academic_verbal,
        math_score, science_score,
        hours, logical_quotient, projects_count, technical_skill_rating, public_speaking,
        comm_skill, logical_ability, technical_skill,
        r_score, i_score, a_score, s_score, e_score, c_score,
        sr_no, course,
        linguistic, musical, bodily, logical_mathematical, spatial_visualization,
        interpersonal, intrapersonal, naturalist,
    ]
    return np.array(features, dtype=np.float64)


def get_feature_names() -> List[str]:
    """Return feature column names in the order expected by the combined model."""
    manifest_path = config.FEATURE_MANIFEST_PATH
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        if "feature_names" in manifest:
            return manifest["feature_names"]
    # Fallback: general feature schema from merge script (matches combined_career_dataset)
    return [
        "Academic_Quantitative", "Academic_Technical", "Academic_Verbal",
        "Math_Score", "Science_Score",
        "Hours_working_per_day", "Logical_quotient_rating", "Projects_Count",
        "Technical_Skill_Rating", "public_speaking_points",
        "Communication_Skill", "Logical_Ability", "Technical_Skill",
        "R_score", "I_score", "A_score", "S_score", "E_score", "C_score",
        "Sr.No.", "Course",
        "Linguistic", "Musical", "Bodily", "Logical_Mathematical", "Spatial_Visualization",
        "Interpersonal", "Intrapersonal", "Naturalist",
    ]


def uses_combined_model() -> bool:
    """Check if the deployed model is the combined (tabular) model."""
    manifest_path = config.FEATURE_MANIFEST_PATH
    if not manifest_path.exists():
        return False
    manifest = read_json(manifest_path)
    return manifest.get("model_type") == "combined_tabular"
