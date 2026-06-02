"""
Builds a beginner-friendly study guide PDF that explains every part of the
Results and Discussion chapter of the thesis manuscript.

Outputs: study_guide_results_and_discussion.pdf at the project root.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = PROJECT_ROOT / "figures"
OUTPUT_PDF = PROJECT_ROOT / "study_guide_results_and_discussion.pdf"


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

base_styles = getSampleStyleSheet()

styles = {
    "title": ParagraphStyle(
        name="Title",
        parent=base_styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1f3a68"),
        spaceAfter=14,
    ),
    "subtitle": ParagraphStyle(
        name="Subtitle",
        parent=base_styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#444444"),
        spaceAfter=22,
    ),
    "h1": ParagraphStyle(
        name="H1",
        parent=base_styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1f3a68"),
        spaceBefore=18,
        spaceAfter=10,
    ),
    "h2": ParagraphStyle(
        name="H2",
        parent=base_styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1f3a68"),
        spaceBefore=14,
        spaceAfter=6,
    ),
    "h3": ParagraphStyle(
        name="H3",
        parent=base_styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2a5594"),
        spaceBefore=10,
        spaceAfter=4,
    ),
    "body": ParagraphStyle(
        name="Body",
        parent=base_styles["BodyText"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    ),
    "bullet": ParagraphStyle(
        name="Bullet",
        parent=base_styles["BodyText"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        alignment=TA_LEFT,
        leftIndent=18,
        bulletIndent=4,
        spaceAfter=4,
    ),
    "callout": ParagraphStyle(
        name="Callout",
        parent=base_styles["BodyText"],
        fontName="Helvetica-Oblique",
        fontSize=10.5,
        leading=15,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor("#333333"),
        backColor=colors.HexColor("#f1f5fb"),
        borderColor=colors.HexColor("#1f3a68"),
        borderPadding=8,
        borderWidth=0.5,
        spaceBefore=4,
        spaceAfter=10,
    ),
    "caption": ParagraphStyle(
        name="Caption",
        parent=base_styles["BodyText"],
        fontName="Helvetica-Oblique",
        fontSize=9.5,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
        spaceAfter=12,
    ),
    "q": ParagraphStyle(
        name="Q",
        parent=base_styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#1f3a68"),
        spaceBefore=8,
        spaceAfter=2,
    ),
    "a": ParagraphStyle(
        name="A",
        parent=base_styles["BodyText"],
        fontName="Helvetica",
        fontSize=11,
        leading=15.5,
        alignment=TA_JUSTIFY,
        leftIndent=14,
        spaceAfter=6,
    ),
    "footer": ParagraphStyle(
        name="Footer",
        parent=base_styles["BodyText"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#777777"),
        alignment=TA_CENTER,
    ),
    "cell": ParagraphStyle(
        name="Cell",
        parent=base_styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
        spaceAfter=0,
        spaceBefore=0,
    ),
    "cell_bold": ParagraphStyle(
        name="CellBold",
        parent=base_styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
        textColor=colors.white,
        spaceAfter=0,
        spaceBefore=0,
    ),
    "cell_center": ParagraphStyle(
        name="CellCenter",
        parent=base_styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=13,
        alignment=TA_CENTER,
        spaceAfter=0,
        spaceBefore=0,
    ),
    "cell_center_bold": ParagraphStyle(
        name="CellCenterBold",
        parent=base_styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        alignment=TA_CENTER,
        spaceAfter=0,
        spaceBefore=0,
    ),
}


def C(text: str, style_key: str = "cell") -> Paragraph:
    """Wrap a string in a Paragraph so the table can wrap text and render entities."""
    return Paragraph(text, styles[style_key])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def P(text: str) -> Paragraph:
    return Paragraph(text, styles["body"])


def H1(text: str) -> Paragraph:
    return Paragraph(text, styles["h1"])


def H2(text: str) -> Paragraph:
    return Paragraph(text, styles["h2"])


def H3(text: str) -> Paragraph:
    return Paragraph(text, styles["h3"])


def Callout(text: str) -> Paragraph:
    return Paragraph(text, styles["callout"])


def Bullets(items: List[str]):
    return [Paragraph(f"&bull;&nbsp;&nbsp;{item}", styles["bullet"]) for item in items]


def NumberedList(items: List[str]):
    return [
        Paragraph(f"<b>{i + 1}.</b>&nbsp;&nbsp;{item}", styles["bullet"])
        for i, item in enumerate(items)
    ]


def figure_block(filename: str, caption: str, width_inches: float = 5.4):
    """Return a flowable block: figure + caption, kept together if possible."""
    path = FIGURES_DIR / filename
    if not path.exists():
        return [Paragraph(f"<i>[Missing figure: {filename}]</i>", styles["caption"])]
    img = Image(str(path), width=width_inches * inch, height=width_inches * 0.72 * inch, kind="proportional")
    cap = Paragraph(caption, styles["caption"])
    return [KeepTogether([img, cap])]


def Q(question: str) -> Paragraph:
    return Paragraph(question, styles["q"])


def A(answer: str) -> Paragraph:
    return Paragraph(answer, styles["a"])


# ---------------------------------------------------------------------------
# Page template (with footer)
# ---------------------------------------------------------------------------


def _draw_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Oblique", 9)
    canvas.setFillColor(colors.HexColor("#777777"))
    footer_text = (
        "Study Guide — Results and Discussion  |  "
        "Personalized Career Recommendation System  |  Page %d"
        % doc.page
    )
    canvas.drawCentredString(LETTER[0] / 2.0, 0.5 * inch, footer_text)
    canvas.restoreState()


def build_pdf():
    doc = BaseDocTemplate(
        str(OUTPUT_PDF),
        pagesize=LETTER,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
        title="Study Guide – Results and Discussion",
        author="Jourdan Ken D. Catarina",
    )
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="normal",
    )
    doc.addPageTemplates(
        [PageTemplate(id="main", frames=[frame], onPage=_draw_footer)]
    )

    story = []
    story.extend(make_title_page())
    story.append(PageBreak())
    story.extend(make_table_of_contents())
    story.append(PageBreak())
    story.extend(make_section_orientation())
    story.append(PageBreak())
    story.extend(make_section_terms())
    story.append(PageBreak())
    story.extend(make_section_setup())
    story.append(PageBreak())
    story.extend(make_section_baselines())
    story.append(PageBreak())
    story.extend(make_section_headline())
    story.append(PageBreak())
    story.extend(make_section_calibration())
    story.append(PageBreak())
    story.extend(make_section_confusion())
    story.append(PageBreak())
    story.extend(make_section_pr())
    story.append(PageBreak())
    story.extend(make_section_roc())
    story.append(PageBreak())
    story.extend(make_section_f1())
    story.append(PageBreak())
    story.extend(make_section_tsne())
    story.append(PageBreak())
    story.extend(make_section_employee())
    story.append(PageBreak())
    story.extend(make_section_leakage())
    story.append(PageBreak())
    story.extend(make_section_overall())
    story.append(PageBreak())
    story.extend(make_section_limits())
    story.append(PageBreak())
    story.extend(make_section_cheatsheet())
    story.append(PageBreak())
    story.extend(make_section_questions())

    doc.build(story)
    print(f"Wrote: {OUTPUT_PDF}")


# ---------------------------------------------------------------------------
# Content sections
# ---------------------------------------------------------------------------


def make_title_page():
    out = [
        Spacer(1, 0.6 * inch),
        Paragraph("Results &amp; Discussion", styles["title"]),
        Paragraph(
            "A Beginner-Friendly Study Guide",
            styles["subtitle"],
        ),
        Spacer(1, 0.15 * inch),
        Paragraph(
            "Personalized Career Recommendation System for Filipino Senior High School Students",
            styles["caption"],
        ),
        Spacer(1, 0.4 * inch),
        Callout(
            "<b>How to use this guide.</b> Read it top to bottom. Each section first "
            "explains the <i>idea</i> behind what we did, then explains what the table "
            "or figure shows, and finally tells you what it means and what to say if "
            "someone asks. By the end you will be able to answer questions about every "
            "number, every graph, and every claim in the Results and Discussion chapter "
            "of the thesis."
        ),
        Spacer(1, 0.2 * inch),
        Callout(
            "<b>One golden sentence to memorize.</b> &ldquo;Our test scores are extremely "
            "high (around 99.8% top-1) on the prepared dataset, but the task was already "
            "easy in that data — a simple logistic regression also hit 99.3% on the "
            "same split — so this is an internal sanity check that the pipeline "
            "works, not yet proof that the system will work for real Senior High School "
            "students.&rdquo;"
        ),
        Spacer(1, 0.4 * inch),
        Paragraph(
            "Prepared as a self-study companion to <i>manuscript.tex</i>, Chapter&nbsp;4 "
            "(Results and Discussion).",
            styles["caption"],
        ),
    ]
    return out


def make_table_of_contents():
    items = [
        "1.  Big-picture orientation (what the chapter is really doing)",
        "2.  Terms you must know before reading anything else",
        "3.  Experimental setup: what data, what split, what seed",
        "4.  Comparison with baselines (Table&nbsp;1)",
        "5.  Headline accuracy numbers (Table&nbsp;2)",
        "6.  Calibration: are the confidence scores honest? (Reliability curve)",
        "7.  Where the system made mistakes (Confusion matrix)",
        "8.  Per-class performance (Precision and recall)",
        "9.  Separability check (ROC curves and AUC)",
        "10. Overall per-class health (F1 score chart)",
        "11. A visual map of the data (t-SNE embedding)",
        "12. Extra real-world check (Employee validation)",
        "13. Robustness checks we still need to do (leakage, ablations)",
        "14. Overall meaning &amp; what readers should NOT conclude",
        "15. Honest limits of the evaluation",
        "16. One-page cheat sheet (memorize before the defense)",
        "17. Top 15 likely defense questions with short answers",
    ]
    return [
        Paragraph("Table of Contents", styles["h1"]),
        Spacer(1, 0.1 * inch),
        *[
            Paragraph(item, styles["body"])
            for item in items
        ],
    ]


def make_section_orientation():
    return [
        H1("1. Big-picture orientation"),
        P(
            "Before diving into numbers, you need to know <b>what the chapter is "
            "actually proving and what it is not proving</b>. If you only remember "
            "two things from this whole guide, remember these:"
        ),
        Callout(
            "<b>Claim A (what we proved).</b> Inside the prepared dataset, the trained "
            "model can almost perfectly recover the career category that was already "
            "written on each row. Top-1 accuracy is ~99.8%, top-3 is ~99.9%, and the "
            "confidence numbers it shows are well-calibrated.<br/><br/>"
            "<b>Claim B (what we did NOT prove).</b> We did <i>not</i> prove the system "
            "predicts what a real Filipino Senior High School (SHS) student will end "
            "up doing as a career. That would require a different study with real "
            "students, with real outcomes verified over time."
        ),
        H2("What is being tested in Chapter 4?"),
        P(
            "The thesis builds a system that has three pieces glued together:"
        ),
        *Bullets([
            "A <b>30-item questionnaire</b> that the user answers in the web app.",
            "A <b>mapping</b> (a fixed set of rules) that converts those 30 answers into "
            "29 numbers (subject scores, RIASEC scores, skill ratings, etc.).",
            "A <b>classifier</b> (XGBoost with isotonic calibration) that takes those 29 "
            "numbers and predicts one of 14 career categories.",
        ]),
        P(
            "Chapter 4 only tests the <b>third piece</b> — the classifier — on "
            "data that already has 29 numbers and 14 career labels filled in. "
            "Specifically, it tests it on a 20% slice of the merged training data that "
            "was set aside before training (the <b>holdout</b> or <b>test set</b>). The "
            "questionnaire and the mapping are <b>not</b> tested in this chapter; that "
            "is left as future work."
        ),
        H2("Why is that important?"),
        P(
            "Because if a panelist asks you &ldquo;99.8% accuracy — does that mean "
            "the system is 99.8% accurate for real students?&rdquo; the correct answer "
            "is <b>no</b>. It is 99.8% accurate at recovering the rule-based label on a "
            "20% slice of the same prepared dataset it was trained on. That is an "
            "engineering sanity check, not a real-world validity claim. The thesis is "
            "transparent about this and so should you."
        ),
        H2("How the chapter is organized"),
        P(
            "The chapter has two halves:"
        ),
        *NumberedList([
            "<b>Results</b> — the raw numbers and figures, with very short "
            "descriptions.",
            "<b>Discussion</b> — the &ldquo;so what?&rdquo; explanations: why each "
            "result looks the way it does, and what we should and should not conclude.",
        ]),
        P(
            "This guide will go through each result, show the figure, and then unpack "
            "the discussion for it. By the end you will be able to answer any question "
            "about any of the tables and figures."
        ),
    ]


def make_section_terms():
    raw_rows = [
        ("Term", "Beginner-friendly meaning"),
        (
            "Top-1 accuracy",
            "Out of every 100 test rows, how many had the model&rsquo;s SINGLE best "
            "guess equal to the correct label.",
        ),
        (
            "Top-3 accuracy",
            "Out of every 100 test rows, how many had the correct label appear "
            "somewhere in the model&rsquo;s 3 best guesses. The product shows 3 "
            "recommendations, so this is the natural product-level metric.",
        ),
        (
            "Precision (for a class)",
            "When the model picks class X, how often is it actually class X? "
            "Penalises FALSE ALARMS.",
        ),
        (
            "Recall (for a class)",
            "Out of all the true class X rows, how many did the model actually find? "
            "Penalises MISSES.",
        ),
        (
            "F1 score",
            "A single number that combines precision and recall (their harmonic "
            "mean). Goes down if either one is weak. Range 0&ndash;1.",
        ),
        (
            "Macro F1",
            "Average F1 across all 14 classes, where every class counts the same. "
            "Useful when classes are unbalanced.",
        ),
        (
            "Weighted F1",
            "Average F1 across all 14 classes, weighted by how many rows each class "
            "has. Big classes pull the average more.",
        ),
        (
            "Confusion matrix",
            "A 14&times;14 grid: rows = true class, columns = predicted class. "
            "Diagonal cells = correct. Off-diagonal cells = mistakes.",
        ),
        (
            "ROC curve",
            "A curve that plots how the model trades off catching positives "
            "vs raising false alarms as you change the decision threshold.",
        ),
        (
            "AUC (ROC AUC)",
            "Area Under the ROC Curve. Measures RANKING ability: probability that the "
            "model gives a higher score to a random positive than a random negative. "
            "0.5 = random, 1.0 = perfect.",
        ),
        (
            "One-vs-rest",
            "A way of using a binary metric (like AUC) on a multi-class problem: do "
            "it 14 times, once per class against &lsquo;everything else&rsquo;, then "
            "average.",
        ),
        (
            "Calibration",
            "Whether the probability the model SHOWS matches reality. If it says "
            "&ldquo;80% sure&rdquo; on 1000 cases, about 800 of them should really be "
            "correct.",
        ),
        (
            "ECE (Expected Calibration Error)",
            "Number between 0 and 1. Difference between predicted probability and "
            "actual accuracy, averaged across bins. Smaller = more honest.",
        ),
        (
            "Brier score",
            "Another calibration / accuracy metric for probabilities. Mean squared "
            "error between predicted probability and the true outcome (0 or 1). "
            "Smaller = better.",
        ),
        (
            "Isotonic regression",
            "The exact technique used to fix probability calibration. A flexible "
            "non-decreasing function fit on a held-out slice that re-maps raw "
            "probabilities into honest ones.",
        ),
        (
            "Stratified split",
            "When we cut data into train/test, we keep the same class proportions on "
            "both sides. Prevents tiny classes from disappearing from the test set.",
        ),
        (
            "Holdout",
            "The 20% slice of the merged dataset that we hide from training and only "
            "use at the very end to grade the model.",
        ),
        (
            "XGBoost",
            "An implementation of gradient-boosted decision trees. It builds many "
            "small trees in sequence, each one trying to fix the mistakes of the "
            "previous ones.",
        ),
        (
            "Baseline",
            "A simple method used as a yardstick. If our fancy method does not beat "
            "the baseline, the fancy method is not really doing anything useful.",
        ),
        (
            "Dataset shift",
            "When the data you train on looks different from the data you actually "
            "deploy on. The classic reason for a model to look great in testing and "
            "then fail in the real world.",
        ),
        (
            "Information leakage",
            "When something you should only know at test-time accidentally appears "
            "during training. Inflates test scores artificially.",
        ),
        (
            "t-SNE",
            "A method that squeezes very complex (high-dimensional) data down to 2 "
            "dimensions so we can look at it. Useful for visualization only; distances "
            "in the picture are not exact.",
        ),
    ]
    # First row is header (bold, white text). Remaining rows use the body cell style.
    header_row = [C(raw_rows[0][0], "cell_bold"), C(raw_rows[0][1], "cell_bold")]
    body_rows = [[C(term, "cell"), C(meaning, "cell")] for term, meaning in raw_rows[1:]]
    rows = [header_row] + body_rows
    table = Table(rows, colWidths=[1.7 * inch, 4.5 * inch], hAlign="LEFT", repeatRows=1)
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a68")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("LEADING", (0, 0), (-1, -1), 13),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f6f8fb"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )

    return [
        H1("2. Terms you must know first"),
        P(
            "Every figure and number in the chapter uses some of these terms. Read "
            "this once and the rest of the guide will feel obvious. Each definition "
            "is written for someone who has never taken a machine-learning class."
        ),
        Spacer(1, 0.08 * inch),
        table,
        Spacer(1, 0.15 * inch),
        Callout(
            "<b>Mini quiz to test yourself:</b><br/>"
            "&bull; If the model says &ldquo;90% sure&rdquo; on 1000 cases and only 600 "
            "are right, is calibration good or bad? &mdash; <i>Bad: it is over-confident.</i><br/>"
            "&bull; If a class has high recall but low precision, what is happening? "
            "&mdash; <i>The model labels too many things as that class. It catches the "
            "true ones (high recall) but also drags in false alarms (low precision).</i><br/>"
            "&bull; Why do we report macro F1, not just accuracy? &mdash; <i>Because "
            "accuracy can hide a class that is doing badly if other classes are big "
            "and easy.</i>"
        ),
    ]


def make_section_setup():
    return [
        H1("3. Experimental setup"),
        P(
            "Before any number means anything, you need to know <b>what dataset it was "
            "measured on</b> and <b>how the data was split</b>. If a panelist tries to "
            "trip you up, this is usually where they start."
        ),
        H2("What dataset?"),
        P(
            "The training data is built by a script called "
            "<font name='Courier'>merge_career_datasets.py</font>. It takes three "
            "CSV files of real career profiles:"
        ),
        *Bullets([
            "<font name='Courier'>source_academic_percentages_it_suggested_roles.csv</font> &mdash; about 20,000 rows.",
            "<font name='Courier'>source_stem_scores_riasec_career_labels.csv</font> &mdash; about 2,400 rows.",
            "<font name='Courier'>source_career_trajectories_multidisciplinary_fields.csv</font> &mdash; about 9,000 rows.",
        ]),
        P(
            "These add up to <b>31,400 real rows</b>. On top of that, the augmented "
            "build adds <b>14,078 synthetic rows</b> generated from curated &ldquo;gold "
            "profile&rdquo; templates &mdash; one per career category &mdash; with small "
            "Gaussian noise. The synthetic rows exist to cover the parts of feature "
            "space the questionnaire-to-feature mapping is most likely to produce."
        ),
        P(
            "After that, each class is downsampled (capped) to balance them: "
            "Computer Science &amp; Technology is capped at 3,500, Natural Sciences at "
            "1,950, and every other class at 1,800. The final modeling table has "
            "<b>27,050 rows</b>."
        ),
        H2("How was it split?"),
        *NumberedList([
            "<b>80/20 stratified split</b>, random seed 42. That gives 21,640 rows for "
            "training and <b>5,410 rows for the test set</b>. The 20% test set is the "
            "one every number in Chapter 4 is measured on.",
            "Inside the 80% training portion, another <b>15% slice is held back to fit "
            "calibration</b>. The base XGBoost is trained on the remaining 85% of the "
            "training data, then the calibrator (isotonic regression) is fit on that "
            "15% slice.",
            "Inside the 85% block, the hyperparameter search uses <b>5-fold stratified "
            "cross-validation</b>, scored by top-3 accuracy. This is how the best "
            "settings (tree depth, learning rate, etc.) are chosen.",
        ]),
        H2("Which model won?"),
        P(
            "Two model families were tried: XGBoost and LightGBM. <b>XGBoost won</b> on "
            "the cross-validation top-3 score, so XGBoost is the deployed model. After "
            "training, the post-hoc <b>isotonic calibration</b> is wrapped around it "
            "using scikit-learn&rsquo;s <font name='Courier'>CalibratedClassifierCV</font>. "
            "The result is what the API serves."
        ),
        H2("What about the questionnaire?"),
        P(
            "The 30-item questionnaire is NEVER used to train the model. It is only "
            "used at inference time: when a real user answers questions, those answers "
            "are converted into the same 29 numbers, and the trained model is asked to "
            "predict. <b>Chapter 4 does not evaluate this mapping</b>, because doing so "
            "would require a separately labeled sample of students with verified career "
            "outcomes. That is left as future work."
        ),
        Callout(
            "<b>Memorize:</b> &ldquo;Every number in Chapter 4 comes from the same 5,410-row "
            "stratified holdout (random seed 42) of the merged tabular corpus. The "
            "questionnaire is used at inference only and is not evaluated here.&rdquo;"
        ),
    ]


def make_section_baselines():
    raw_rows = [
        ("Model", "Top-1", "Top-3", "Macro F1"),
        ("Uniform random dummy", "0.074", "0.205", "0.073"),
        ("Stratified random dummy", "0.077", "0.210", "0.073"),
        ("Majority class (CS&amp;T)", "0.129", "0.263", "0.016"),
        ("Multinomial logistic regression", "0.993", "1.000", "0.993"),
        ("Random forest (200 trees)", "0.999", "1.000", "0.999"),
        ("XGBoost + isotonic (deployed)", "0.998", "0.999", "0.998"),
    ]
    header = [C(raw_rows[0][0], "cell_bold")] + [C(c, "cell_center_bold") for c in raw_rows[0][1:]]
    body = []
    for i, r in enumerate(raw_rows[1:]):
        bold = i == len(raw_rows) - 2  # last row (deployed model) shown bold
        body.append(
            [C(r[0], "cell")]
            + [C(c, "cell_center") for c in r[1:]]
        )
    rows = [header] + body
    table = Table(
        rows,
        colWidths=[3.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch],
        hAlign="LEFT",
        repeatRows=1,
    )
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a68")),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fff8d6")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.HexColor("#f6f8fb"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )

    return [
        H1("4. Comparison with baselines"),
        H2("What is a baseline and why do we need one?"),
        P(
            "A <b>baseline</b> is a deliberately simple method that we run as a "
            "sanity check. If our advanced method cannot beat a baseline, the "
            "advanced method is not really doing anything useful — the data alone "
            "is doing all the work. So baselines protect us from fooling ourselves."
        ),
        P(
            "The thesis uses five baselines (three trivial, two strong) plus the "
            "deployed model:"
        ),
        *Bullets([
            "<b>Uniform random dummy</b> &mdash; picks any of the 14 classes with equal "
            "probability. Expected top-1 is 1/14 &asymp; 7.1%.",
            "<b>Stratified random dummy</b> &mdash; picks at random but biased toward "
            "common classes. Similar level.",
            "<b>Majority class</b> &mdash; always says &ldquo;Computer Science &amp; "
            "Technology&rdquo; because that is the biggest class.",
            "<b>Multinomial logistic regression</b> &mdash; the classic simple linear "
            "classifier. Very transparent, easy to interpret.",
            "<b>Random forest (200 trees)</b> &mdash; a tree-ensemble model. Strong on "
            "tabular data, but in a different way than XGBoost.",
            "<b>XGBoost + isotonic</b> &mdash; the deployed system.",
        ]),
        H2("What the table actually says"),
        table,
        Spacer(1, 0.1 * inch),
        Callout(
            "<b>Two readings of this table:</b><br/>"
            "<b>1) The reassuring reading.</b> Random guessing got ~7%, exactly what "
            "you would expect on 14 balanced classes. So the test is honest — it is "
            "not handing out high scores for free.<br/><br/>"
            "<b>2) The cautious reading.</b> Logistic regression — a very simple "
            "linear method — already hit <b>99.3%</b> top-1. The fancy XGBoost only "
            "added another 0.5 percentage points. That tells us the task is already "
            "easy in this dataset. Most of the &lsquo;magic&rsquo; is in the way the "
            "data was prepared and labelled, not in the algorithm."
        ),
        H2("How to talk about this in a defense"),
        P(
            "If someone asks &ldquo;why XGBoost if logistic regression already does the "
            "job?&rdquo;, the right answer has two parts:"
        ),
        *NumberedList([
            "XGBoost provides a small but real refinement on the few hard cases, and "
            "more importantly it lets us cleanly attach <i>isotonic calibration</i> on a "
            "held-out slice so the confidence numbers shown to students are honest. "
            "Linear models also calibrate, but tree boosting handles non-linear "
            "interactions between features (like a high R-score and a low S-score "
            "together) more naturally if the data ever becomes harder.",
            "We do not claim XGBoost &lsquo;solved&rsquo; the task. The thesis is "
            "transparent that the engineered feature space is already largely "
            "separable, so the boosting stage refines decision boundaries rather "
            "than uniquely solving the problem.",
        ]),
    ]


def make_section_headline():
    raw_rows = [
        ("Metric", "Value"),
        ("Top-1 Accuracy", "99.8%"),
        ("Top-3 Accuracy", "99.9%"),
        ("Macro F1", "0.998"),
        ("Micro-average ROC AUC (one-vs-rest)", "0.9995"),
        ("Macro-average ROC AUC (one-vs-rest)", "0.9996"),
        ("Model family", "XGBoost (selected over LightGBM)"),
    ]
    header = [C(c, "cell_bold") for c in raw_rows[0]]
    body = [[C(metric, "cell"), C(value, "cell")] for metric, value in raw_rows[1:]]
    rows = [header] + body
    table = Table(rows, colWidths=[3.7 * inch, 2.5 * inch], hAlign="LEFT", repeatRows=1)
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a68")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f6f8fb"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )

    return [
        H1("5. Headline accuracy numbers"),
        H2("What this table answers"),
        P(
            "Once you have established that the test is fair (Section 4), the next "
            "question is &ldquo;how well does the system do overall?&rdquo; That is "
            "what this table summarizes. Every number comes from the same 5,410-row "
            "holdout."
        ),
        table,
        Spacer(1, 0.1 * inch),
        H2("What each row means in plain language"),
        *Bullets([
            "<b>Top-1 = 99.8%</b>. Out of 5,410 test rows, only <b>9</b> were given the "
            "wrong category as the SINGLE best guess.",
            "<b>Top-3 = 99.9%</b>. If we allow the system to show three suggestions "
            "(which it does in the UI), almost every case is covered. This is why the "
            "product is designed to show three.",
            "<b>Macro F1 = 0.998</b>. Averaged across all 14 classes (each counted "
            "equally), the model still scores essentially perfect. No single class is "
            "dragging the average down.",
            "<b>Micro-average ROC AUC = 0.9995</b>. Treats all rows the same. Measures "
            "ranking quality: how well the model separates each class from all the "
            "rest. Near-perfect.",
            "<b>Macro-average ROC AUC = 0.9996</b>. Same idea but averaged across the "
            "14 one-vs-rest binary problems. Confirms no class is failing.",
            "<b>Model family</b>. We tried XGBoost and LightGBM; XGBoost won the "
            "5-fold CV on top-3 accuracy, so it is the deployed model.",
        ]),
        H2("Why top-3 is higher than top-1"),
        P(
            "Because giving three guesses is always easier than giving one. Whenever "
            "the model is even slightly uncertain about a profile, the correct answer "
            "usually still sits in second or third place. Top-3 catches those "
            "borderline cases. That is also exactly why we display three options to "
            "the user — it adds a small safety margin at almost no cost."
        ),
        Callout(
            "<b>How to read these numbers in your defense:</b> &ldquo;These are headline "
            "metrics on the 20% holdout of the merged corpus. They show the classifier "
            "recovers the rule-based category nearly perfectly inside that data "
            "distribution. They do not yet show what will happen with real SHS "
            "students.&rdquo;"
        ),
    ]


def make_section_calibration():
    blocks = [
        H1("6. Calibration: are the confidence scores honest?"),
        H2("What problem does this solve?"),
        P(
            "The product does not just say &ldquo;your top career is Engineering&rdquo;. "
            "It also shows a percentage, like &ldquo;85% likely&rdquo;. That number is "
            "supposed to mean something. If we collected all the cases where the model "
            "said &ldquo;85% likely&rdquo;, ideally about 85% of them would actually be "
            "correct. When that happens, we say the model is <b>well calibrated</b>."
        ),
        P(
            "Why is this important? Because if the model is over-confident (says 90% "
            "sure but is only right 60% of the time), users will trust recommendations "
            "they should not. In a guidance setting, that could push a student toward "
            "a career field that doesn&rsquo;t actually match them."
        ),
        H2("How we made the model honest"),
        P(
            "Raw XGBoost probabilities are not always well calibrated. So we use a "
            "two-step trick:"
        ),
        *NumberedList([
            "Hide 15% of the training data before the model sees it. Train XGBoost on "
            "the remaining 85%.",
            "Then fit an <b>isotonic regression</b> calibrator on that hidden 15%. "
            "Isotonic regression is a non-decreasing step function that re-maps raw "
            "probabilities into honest ones (e.g. &ldquo;raw 0.9 should really be "
            "treated as 0.78&rdquo;).",
            "Wrap both together with scikit-learn&rsquo;s "
            "<font name='Courier'>CalibratedClassifierCV(method=&quot;isotonic&quot;)</font>. "
            "This is what the API serves.",
        ]),
        H2("How we measured calibration"),
        *Bullets([
            "<b>Expected Calibration Error (ECE)</b>. Group predictions into bins by "
            "confidence (e.g. 0&ndash;10%, 10&ndash;20%, ...). For each bin, compare "
            "the average predicted probability vs. the actual accuracy. Average the "
            "absolute gap across all bins. <b>Smaller = better; 0 = perfect.</b>",
            "<b>Brier score</b>. Mean squared error between the predicted probability "
            "of each class and the indicator of whether that class was actually the "
            "true one. Also smaller = better.",
        ]),
        H2("What we got"),
        P(
            "<b>ECE &asymp; 0.0002</b> and <b>Brier &asymp; 0.0027</b>. The target in "
            "the thesis methodology was ECE &le; 0.10. We are about 500&times; better "
            "than the target. Below is the reliability curve."
        ),
    ]
    blocks.extend(
        figure_block(
            "reliability_curve.png",
            "Figure 1 (Reliability curve). Dots compare the confidence the system stated "
            "with how often it was actually correct. The dashed line is what a perfectly "
            "honest model would look like. Dots near the line = good calibration.",
        )
    )
    blocks.extend([
        H2("What this curve is and how to read it"),
        *Bullets([
            "<b>Horizontal axis:</b> the confidence the model SHOWED (its predicted "
            "probability for its top guess).",
            "<b>Vertical axis:</b> the fraction of those cases that were ACTUALLY "
            "correct.",
            "<b>Dashed diagonal:</b> the line of perfect calibration (predicted = "
            "actual).",
            "<b>Dots above the line:</b> the model is UNDER-confident (it&rsquo;s right "
            "more often than it claims).",
            "<b>Dots below the line:</b> the model is OVER-confident (it&rsquo;s right "
            "less often than it claims).",
        ]),
        H2("Why the curve looks like this"),
        P(
            "Two reasons:"
        ),
        *NumberedList([
            "We deliberately calibrated the model using isotonic regression, so we "
            "have explicitly forced predicted probabilities to line up with empirical "
            "accuracy on a held-out slice.",
            "The data itself is so easy that the model is rarely uncertain. Most of "
            "its predictions sit at very high confidence. So most of the dots are "
            "bunched at the right end of the plot.",
        ]),
        Callout(
            "<b>Honest caveat to know:</b> the LEFT half of the curve (low / medium "
            "confidence) is based on very few cases, because the model is rarely "
            "unsure on this dataset. So the middle of the curve should not be taken as "
            "strong evidence by itself. The headline message is &lsquo;at the "
            "high-confidence end where most predictions live, predicted matches "
            "actual.&rsquo;"
        ),
        H2("How to defend this"),
        P(
            "&ldquo;The system shows calibrated probabilities to users so it can give "
            "an honest sense of confidence. We measured calibration with ECE (~0.0002) "
            "and Brier (~0.0027), well below our 0.10 target. The combination of "
            "isotonic post-hoc calibration and an already-separable feature space "
            "explains why the calibration is so tight on this holdout. Whether it "
            "stays this tight with real student answers is a question for the future "
            "external validation study.&rdquo;"
        ),
    ])
    return blocks


def make_section_confusion():
    blocks = [
        H1("7. Where the system made mistakes (Confusion matrix)"),
        H2("What is a confusion matrix?"),
        P(
            "It is a square table that has one row for every TRUE class and one "
            "column for every PREDICTED class. Each cell counts how many test "
            "rows fell into that (true, predicted) pair. The diagonal counts "
            "correct predictions. Everything off the diagonal counts mistakes, "
            "and the SHAPE of the off-diagonal pattern tells us a story."
        ),
        H2("Why do we need it?"),
        P(
            "Pure accuracy gives one number, which hides which classes are getting "
            "confused with which. A confusion matrix lets us answer detailed "
            "diagnostic questions like:"
        ),
        *Bullets([
            "Which class pairs does the model mix up most?",
            "Is there a single class that acts as a &lsquo;dumping ground&rsquo; for "
            "uncertain predictions?",
            "Are mistakes spread evenly, or concentrated?",
            "Should we change the questionnaire to better separate the confused "
            "pair?",
        ]),
    ]
    blocks.extend(
        figure_block(
            "confusion_matrix.png",
            "Figure 2 (Confusion matrix). Rows = true career category, columns = "
            "predicted career category. Diagonal cells = correct. The matrix is almost "
            "entirely diagonal: only 9 of 5,410 holdout rows were misclassified.",
            width_inches=6.2,
        )
    )
    blocks.extend([
        H2("Reading the result"),
        P(
            "On the 5,410-row holdout, only <b>9 rows</b> were misclassified. The "
            "specific mistakes form an interesting pattern, not random noise:"
        ),
        *Bullets([
            "<b>Education / Teaching &rarr; Medicine</b> happened <b>4 times</b>. This "
            "is the most common single error.",
            "<b>Computer Science &amp; Technology</b> had 4 scattered errors: 2 went "
            "to Accounting &amp; Finance, 1 to Medicine, 1 to Natural Sciences.",
            "<b>Arts &amp; Design &rarr; Education / Teaching</b> happened 1 time.",
            "All other rows in the test set were classified correctly.",
        ]),
        H2("Why these specific errors?"),
        *Bullets([
            "<b>Education vs. Medicine</b> overlap because both involve "
            "&lsquo;working with people&rsquo; AND &lsquo;studying / investigating&rsquo;. "
            "Some profiles really do look similar in the 29-feature space.",
            "<b>Computer Science scatter</b> is mostly a size effect: it is the "
            "biggest class (3,500 rows before split, 700 rows in the holdout), so it "
            "naturally contains more unusual profiles that sit near borderlines.",
        ]),
        H2("What to take away"),
        Callout(
            "&ldquo;The mistakes are rare and explainable, not random. They concentrate "
            "in semantically adjacent fields (Education/Medicine) and in the biggest "
            "class (CS&amp;T). If we wanted to push accuracy further, we would target "
            "those specific pairs by adding questionnaire items that better separate "
            "&lsquo;working-with-people-on-health&rsquo; from "
            "&lsquo;working-with-people-on-learning&rsquo;, rather than tuning the "
            "model further.&rdquo;"
        ),
    ])
    return blocks


def make_section_pr():
    blocks = [
        H1("8. Per-class performance: Precision and recall"),
        H2("Why look at this if accuracy is already near 100%?"),
        P(
            "Because accuracy is just one number for the whole model. Per-class "
            "precision and recall let us check that every class is healthy. A small "
            "weakness in one class might be invisible in the average but matter a lot "
            "for the students in that field."
        ),
        H2("Definitions, again, but with stakes"),
        *Bullets([
            "<b>Precision</b> for class X = &ldquo;when the model picks X, how often "
            "is it right?&rdquo; Low precision means the model FALSELY puts people "
            "into X.",
            "<b>Recall</b> for class X = &ldquo;out of the rows that are truly X, how "
            "many did the model catch?&rdquo; Low recall means the model MISSES "
            "people who really belong to X.",
            "In a career-guidance setting, low precision could push the wrong "
            "students into a field; low recall could mean students who would have "
            "loved a field never get it recommended. Both matter.",
        ]),
    ]
    blocks.extend(
        figure_block(
            "precision_recall.png",
            "Figure 3 (Precision and recall per class). Both metrics are near 1.0 for "
            "all 14 categories. The visible dips are concentrated in the categories "
            "involved in the few mistakes (Medicine, CS&T, Education, Arts).",
        )
    )
    blocks.extend([
        H2("What the chart shows"),
        *Bullets([
            "Average precision and recall across all 14 classes = <b>0.998</b>.",
            "8 of the 14 classes scored <b>perfect 1.0</b> on both.",
            "<b>Lowest precision: Medicine (~0.986)</b>. Reason: 5 rows from other "
            "classes were wrongly placed into Medicine (4 from Education, 1 from "
            "CS&amp;T). Medicine was acting as a slight &lsquo;dumping ground&rsquo;.",
            "<b>Lowest recall: CS&amp;T (~0.994)</b>. Reason: 4 of its own rows "
            "leaked out into other categories (Accounting, Medicine, Natural "
            "Sciences). This is the size effect from the biggest class.",
            "<b>Education recall &asymp; 0.989</b>. Same root cause as Medicine&rsquo;s "
            "precision dip: those 4 Education rows were misread as Medicine.",
            "<b>Arts &amp; Design recall &asymp; 0.997</b> from one Arts row going "
            "to Education.",
        ]),
        H2("The key insight"),
        P(
            "Precision and recall are TWO ANGLES on the same 9 mistakes. Every error "
            "lowers the recall of the true class AND lowers the precision of the "
            "predicted class. So the precision/recall chart is just a different view "
            "of the confusion matrix; consistent with everything else."
        ),
        Callout(
            "<b>Defense soundbite:</b> &ldquo;Per-class precision and recall both "
            "average 0.998 with no class below 0.986. The few small dips trace "
            "exactly to the 9 misclassifications in the confusion matrix and do not "
            "indicate a systematic weakness for any career category.&rdquo;"
        ),
    ])
    return blocks


def make_section_roc():
    blocks = [
        H1("9. ROC curves and AUC"),
        H2("What is an ROC curve?"),
        P(
            "Imagine the model is a yes/no detector for one class at a time, say "
            "&ldquo;is this row Engineering?&rdquo;. By varying a probability threshold "
            "(only call it Engineering if the probability is &gt; 0.3, or &gt; 0.5, or "
            "&gt; 0.9, etc.), we trade off two things:"
        ),
        *Bullets([
            "<b>True positive rate (TPR)</b> = recall = how many real Engineers we "
            "catch.",
            "<b>False positive rate (FPR)</b> = how many non-Engineers we wrongly "
            "label as Engineers.",
        ]),
        P(
            "Plot TPR on the y-axis and FPR on the x-axis as the threshold sweeps "
            "from 0 to 1. That curve is the <b>ROC curve</b>. A perfect classifier "
            "shoots up to (0, 1) immediately. A random classifier sits on the diagonal "
            "from (0, 0) to (1, 1)."
        ),
        H2("What is AUC?"),
        P(
            "AUC = Area Under the Curve. It is a single number from 0 to 1 that "
            "summarises the ROC curve. AUC has a nice interpretation: it is the "
            "probability that the model gives a higher score to a random positive "
            "case than to a random negative case. So AUC = 0.5 means random ranking; "
            "AUC = 1.0 means perfect ranking; AUC &lt; 0.5 means it&rsquo;s actively "
            "wrong."
        ),
        H2("How do we use it with 14 classes?"),
        P(
            "Two standard tricks (both are reported):"
        ),
        *Bullets([
            "<b>One-vs-rest, macro-averaged</b>: compute AUC for each class against "
            "&lsquo;everything else&rsquo;, then average those 14 numbers equally. "
            "Treats small and big classes the same.",
            "<b>One-vs-rest, micro-averaged</b>: lump everything together and compute "
            "one big AUC over all (class, prediction) pairs. Big classes dominate.",
        ]),
    ]
    blocks.extend(
        figure_block(
            "roc_auc_multi.png",
            "Figure 4 (ROC curves, one per class). All curves sit in the top-left "
            "corner, indicating near-perfect separation. Macro-average AUC = 0.9996, "
            "micro-average AUC = 0.9995.",
        )
    )
    blocks.extend([
        H2("What this figure shows for us"),
        *Bullets([
            "Every curve hugs the top-left corner, the &lsquo;perfect&rsquo; region.",
            "Macro AUC = <b>0.9996</b>, micro AUC = <b>0.9995</b>. So whether you "
            "weight by class size or not, ranking quality is essentially perfect.",
            "All 14 classes are individually separable from the rest. No class is "
            "weak on ranking.",
        ]),
        H2("Honest caveat"),
        P(
            "When AUC is already this saturated, it stops giving new information. It "
            "is included for completeness (because reviewers expect to see it for a "
            "multi-class classifier) but the more useful diagnostics here are the "
            "confusion matrix, the calibration curve, and the per-class F1 chart."
        ),
        Callout(
            "<b>Defense soundbite:</b> &ldquo;ROC curves show that, even at any chosen "
            "probability threshold, the model ranks the correct class above the "
            "others nearly perfectly for every one of the 14 categories. We report "
            "both macro and micro AUC because they answer slightly different "
            "questions and they agree.&rdquo;"
        ),
    ])
    return blocks


def make_section_f1():
    blocks = [
        H1("10. F1 score per class"),
        H2("What is F1 and why do we need it after precision/recall?"),
        P(
            "F1 is the harmonic mean of precision and recall. The harmonic mean has a "
            "useful property: it gets dragged down by the smaller of the two. So if a "
            "class has high precision but low recall (or vice versa), its F1 will "
            "fall, not stay artificially high."
        ),
        P(
            "That makes F1 the right single-number &lsquo;health metric&rsquo; per "
            "class. The macro-F1 (average across the 14 classes, equal weight) was "
            "already in the headline table; this chart breaks that one number down "
            "into per-class bars."
        ),
    ]
    blocks.extend(
        figure_block(
            "f1_score.png",
            "Figure 5 (F1 per class). Every bar sits near 1.0. The two slightly lower "
            "bars (Medicine and Education / Teaching, ~0.993) are exactly the two "
            "classes involved in the main confusion. The dashed line shows the macro "
            "average (0.998).",
        )
    )
    blocks.extend([
        H2("What to notice"),
        *Bullets([
            "All bars are nearly the same height. No class is failing in silence.",
            "<b>Medicine</b> and <b>Education / Teaching</b> are the two slightly "
            "lower bars (~0.993). Both lose a little to the same confusion pair "
            "(Education &rarr; Medicine).",
            "<b>CS&amp;T</b> is next-lowest (~0.997) because of its scattered "
            "out-of-class errors.",
            "Every class beats the methodology target (&ge; 0.65 per-class F1) by a "
            "huge margin.",
        ]),
        H2("Why include F1 if accuracy is already high?"),
        P(
            "Because F1 is the early-warning detector for future regressions. If we "
            "later change the data, the augmentation recipe, or the questionnaire "
            "mapping, the OVERALL accuracy might still look fine even if one class "
            "quietly collapsed. The per-class F1 chart would show that immediately."
        ),
        Callout(
            "<b>Defense soundbite:</b> &ldquo;Per-class F1 confirms that the model is "
            "balanced. No category is propped up by another. The macro-F1 is 0.998 "
            "and even the weakest classes (Medicine and Education at ~0.993) stay "
            "well above our 0.65 target.&rdquo;"
        ),
    ])
    return blocks


def make_section_tsne():
    blocks = [
        H1("11. A visual map of the data (t-SNE)"),
        H2("What is t-SNE?"),
        P(
            "t-SNE (t-distributed Stochastic Neighbor Embedding) is a dimensionality "
            "reduction technique. Our data lives in 29 dimensions (one per feature), "
            "which we cannot draw. t-SNE squeezes it down to 2 dimensions in a way "
            "that tries to keep similar rows near each other and dissimilar rows far "
            "apart. The result is a 2D scatter plot we can look at."
        ),
        H2("Why use it here?"),
        P(
            "To visually check whether the 14 career categories really form distinct "
            "clusters in feature space. If they do, then the classifier&rsquo;s near-"
            "perfect accuracy is unsurprising; the data is already well-separated. If "
            "they didn&rsquo;t, near-perfect accuracy would be very suspicious."
        ),
    ]
    blocks.extend(
        figure_block(
            "tsne_embeddings.png",
            "Figure 6 (t-SNE projection). Each dot is one career profile, colored by "
            "its true career category. Dots of the same color mostly form their own "
            "clear clusters, consistent with the near-perfect classification results.",
            width_inches=5.6,
        )
    )
    blocks.extend([
        H2("Reading the picture"),
        *Bullets([
            "Each dot is one row from the dataset.",
            "Color = true career category.",
            "Clusters of similar color mean those rows look similar in feature space.",
            "Gaps between differently-colored clusters mean the classifier has clear "
            "boundaries to learn.",
        ]),
        H2("Important caveats about t-SNE"),
        Callout(
            "<b>Do NOT use t-SNE as proof of separability.</b> t-SNE squishes 29D into "
            "2D and in doing so it distorts distances. Two clusters that look close "
            "may actually be far apart, and clusters that look far apart may be close. "
            "Cluster sizes and the gaps between them are not faithful to the original "
            "distances. The plot is only included as an intuitive illustration; the "
            "REAL evidence of separability is the confusion matrix and the accuracy "
            "scores, not this picture."
        ),
        H2("How to defend this"),
        P(
            "&ldquo;t-SNE is a visualization only. It shows that the 14 categories "
            "form recognisable clusters in 29D feature space, which is consistent "
            "with the near-perfect accuracy from the classifier. It is not, by itself, "
            "evidence of classification quality — we rely on the confusion matrix, "
            "calibration curve, and per-class F1 for that.&rdquo;"
        ),
    ])
    return blocks


def make_section_employee():
    blocks = [
        H1("12. Extra check with working professionals"),
        H2("Why do this at all?"),
        P(
            "All the metrics above are measured on the prepared dataset. That dataset "
            "trains the model. So if we want even a small piece of evidence that the "
            "deployed system behaves reasonably when REAL people answer the REAL "
            "questionnaire, we need data from outside the dataset."
        ),
        P(
            "That is what the employee validation is. It is a small face-validity "
            "check, not a proper validation study. It is reported with all of its "
            "limitations stated."
        ),
        H2("Exactly what was done"),
        *NumberedList([
            "Working professionals were invited from the researcher&rsquo;s personal "
            "and professional network (this is <b>convenience sampling</b>).",
            "Each participant gave consent, reported their current career and tenure, "
            "and answered the same 30-item questionnaire used by the live system.",
            "After submitting, they were shown the model&rsquo;s top-3 career "
            "predictions with calibrated probabilities.",
            "They answered a single yes/no question: <i>&ldquo;Is your current career "
            "field included in the top-3 predicted careers shown above?&rdquo;</i>",
            "If they answered no, they optionally gave their actual career field and "
            "rated each suggestion 1–5 on relevance.",
            "Low-evidence rows were excluded (a smoke-test session; participants who "
            "said &lsquo;no&rsquo; without supplying their actual field; participants "
            "who said &lsquo;no&rsquo; and rated the top-1 ≤ 2). After exclusions, "
            "<b>N = 30</b> sessions remain.",
            "<b>Headline metric: 86.7% self-reported top-3 hit rate</b> (26 of 30).",
        ]),
    ]
    blocks.extend(
        figure_block(
            "employee_validation.png",
            "Figure 7 (Employee validation, N=30 convenience sample). Left: share of "
            "professionals whose current career field appeared in the top-3 "
            "recommendations (86.7% yes, 13.3% no). Right: same breakdown by tenure "
            "in current career. These responses were never used to train or tune "
            "the model.",
        )
    )
    blocks.extend([
        H2("Why this is encouraging but NOT proof"),
        *Bullets([
            "<b>Convenience sample:</b> participants came from one personal network. "
            "They do not represent the Filipino workforce, and not all 14 categories "
            "are equally represented.",
            "<b>Self-report:</b> participants graded the model on their own field. "
            "&lsquo;Yes&rsquo; just means &lsquo;I saw my field in the top 3&rsquo;. "
            "It does not mean the model is right for OTHER people.",
            "<b>Adults, not SHS students:</b> the target population is teenagers; "
            "these are working professionals.",
            "<b>Small N:</b> with 30 people, the &plusmn; in a 86.7% rate is wide.",
        ]),
        Callout(
            "<b>Defense soundbite:</b> &ldquo;The employee validation is a "
            "supplementary face-validity check. 86.7% top-3 hit rate on a convenience "
            "sample of 30 working professionals is directional evidence that the "
            "deployed pipeline produces plausible outputs when real people take the "
            "questionnaire. It is NOT a substitute for the external validation study "
            "with SHS students that we plan as future work.&rdquo;"
        ),
        H2("Why it lines up with the holdout numbers"),
        P(
            "The 86.7% real-world top-3 hit rate is in the same ballpark as the "
            "99.9% top-3 accuracy on the holdout. It is lower, which is exactly what "
            "we would expect when going from prepared data to real human answers. The "
            "FACT that the numbers point in the same direction is the small piece of "
            "good news here."
        ),
    ])
    return blocks


def make_section_leakage():
    return [
        H1("13. Robustness checks we still need to do"),
        H2("Why even talk about this?"),
        P(
            "Because honest reporting matters. Near-perfect accuracy always raises "
            "the question &ldquo;did the model cheat?&rdquo;, and the chapter must "
            "answer that question head-on. The cheating we&rsquo;re talking about is "
            "called <b>information leakage</b>."
        ),
        H2("What is information leakage?"),
        P(
            "Information leakage is when information that should only be available at "
            "TEST time accidentally ends up in TRAINING time. When that happens, the "
            "test score looks great but the model has just memorised something that "
            "wouldn&rsquo;t exist in the real world."
        ),
        H2("Three specific leakage risks in this project"),
        *Bullets([
            "<b>Duplicate or near-duplicate rows.</b> If almost-identical profile rows "
            "appear in both the training and test slices, the model can &lsquo;ace&rsquo; "
            "the test set by remembering rather than generalising.",
            "<b>Source-file structure.</b> Each CSV has its own characteristic ranges. "
            "If rows from the same CSV land in both train and test, the model can "
            "learn &lsquo;this row smells like Source 2, so probably class X&rsquo; "
            "instead of learning the underlying career signal.",
            "<b>Synthetic-row construction.</b> The augmented rows are generated from "
            "&lsquo;gold profile&rsquo; templates per category, using the same kind of "
            "rules that map answers to features. If those gold profiles ever end up "
            "in the test set too, we&rsquo;re grading the model on its own training "
            "blueprint.",
        ]),
        H2("What we&rsquo;ve done so far"),
        *Bullets([
            "Fixed random seed (42) so the split is repeatable.",
            "Stratified split so class proportions stay the same on both sides.",
            "Honest baseline comparison (Section 4) so an unfair advantage would have "
            "shown up against logistic regression.",
        ]),
        H2("What we STILL need to do (and the chapter says so)"),
        *NumberedList([
            "<b>Duplicate audit.</b> Hash or near-deduplicate rows before splitting.",
            "<b>Source-wise / grouped split.</b> Keep each source file (or each "
            "&lsquo;gold profile&rsquo; cluster) entirely on one side of the split.",
            "<b>Feature-family ablations.</b> Drop entire groups (RIASEC, academic, "
            "skills) and re-train, to see how much each group is actually doing.",
            "<b>SHAP-style attribution.</b> Confirm the model is using features that "
            "make pedagogical sense, not surface artifacts.",
        ]),
        Callout(
            "<b>Defense soundbite:</b> &ldquo;Yes, the holdout accuracy is suspiciously "
            "high. We address that head-on in three ways: (1) by reporting that a "
            "simple logistic regression also reached 99.3%, showing the task is "
            "intrinsically easy in this data, (2) by listing the specific leakage "
            "audits we have NOT yet done as future work, and (3) by refusing to claim "
            "external validity for SHS students from this number alone.&rdquo;"
        ),
    ]


def make_section_overall():
    return [
        H1("14. Overall meaning"),
        H2("If a panelist could only ask one question..."),
        P(
            "It would be: &ldquo;<i>What does this evaluation actually prove?</i>&rdquo; "
            "Here is the answer in one clean paragraph that you should be able to "
            "recite from memory:"
        ),
        Callout(
            "&ldquo;On the prepared dataset, the deployed XGBoost classifier with "
            "isotonic calibration matches the strong simple baselines on accuracy "
            "(~99.8% top-1, ~99.9% top-3, macro-F1 0.998) and is well-calibrated "
            "(ECE &asymp; 0.0002). Its few mistakes are concentrated in a small number "
            "of explainable confusion pairs (Education vs. Medicine, scattered "
            "CS&amp;T). This proves the pipeline works end-to-end on the merged "
            "tabular corpus, and that the engineered feature space is already "
            "largely separable. It does NOT prove the system will recommend correct "
            "careers for real Senior High School students; for that, we need the "
            "external validation studies described in Section 3.7 and Chapter 5.&rdquo;"
        ),
        H2("Three concrete takeaways"),
        *NumberedList([
            "<b>Internal performance is an engineering sanity check.</b> It tells us "
            "the pipeline is plumbed correctly and the model trained without obvious "
            "bugs. It is not a guarantee about the real world.",
            "<b>Most of the lift comes from the data, not the algorithm.</b> A simple "
            "logistic regression already hit 99.3% top-1 on the same split. XGBoost "
            "is the smaller, careful refinement on top, with the added benefit of "
            "supporting clean isotonic calibration.",
            "<b>Outputs are decision support, not deterministic placement.</b> The "
            "system should be talked about (and shown to students) as a "
            "discussion prompt, not as a final answer. This framing is consistent "
            "across the manuscript and the UI.",
        ]),
        H2("What would make the evidence stronger"),
        *Bullets([
            "Run the leakage and ablation audits from Section 13.",
            "Run a real SHS pilot with counselor-rated relevance and student-rated "
            "usefulness as the primary outcomes (these are the proxy criteria for "
            "&lsquo;correctness&rsquo; when adolescents don&rsquo;t have stable "
            "long-run career labels).",
            "Run a longitudinal follow-up after time has passed (alignment with "
            "tertiary course choice, satisfaction, etc.).",
        ]),
    ]


def make_section_limits():
    return [
        H1("15. Honest limits of this evaluation"),
        P(
            "The chapter is deliberately explicit about what these numbers do not "
            "say. The thesis itself reports these limits; if you don&rsquo;t mention "
            "them on your own, panelists will ask. Better to lead with them."
        ),
        H2("Limit 1: distribution mismatch"),
        P(
            "The training data is built from adult-style career profiles (job titles, "
            "skill vectors, RIASEC scores from career corpora). The intended deployment "
            "audience is Filipino SHS students. The two distributions are not the "
            "same: students are still exploring, their self-reports are noisier, and "
            "they don&rsquo;t have a verified &lsquo;true&rsquo; career label yet."
        ),
        H2("Limit 2: the questionnaire-to-feature mapping is not evaluated here"),
        P(
            "Chapter 4 grades the CLASSIFIER on already-prepared 29-dimensional rows. "
            "It does not grade the mapping that converts questionnaire answers into "
            "those 29 numbers. The mapping is a fixed set of heuristic rules. If the "
            "rules over-emphasise or under-emphasise a feature, the live system can "
            "behave differently from the holdout numbers."
        ),
        H2("Limit 3: t-SNE is illustrative only"),
        P(
            "The 2D map cannot be trusted for distances. It supports the claim that "
            "clusters exist but is not itself the evidence."
        ),
        H2("Limit 4: synthetic augmentation"),
        P(
            "About 14k of the rows used for training were synthetic, generated from "
            "gold profile templates. They are intended to stabilise the mapping but "
            "they were created with rules that resemble the labelling logic. Reviewers "
            "are right to ask whether some of the perfect performance is the model "
            "learning its own construction recipe — hence the planned leakage "
            "audits in Section 13."
        ),
        H2("Limit 5: convenience sample for employee validation"),
        P(
            "30 working professionals from the researcher&rsquo;s network do not "
            "represent the Filipino workforce, and they are adults rather than SHS "
            "students. The 86.7% top-3 hit rate is a face-validity signal, not a "
            "population-level validity claim."
        ),
        Callout(
            "<b>Defense soundbite for limits:</b> &ldquo;The evaluation is intentionally "
            "framed as INTERNAL validation. Real SHS-facing claims need a different "
            "study with counselor-rated relevance, student-rated usefulness, alignment "
            "with strand and tertiary plans, and longitudinal follow-up. These are "
            "listed as the next steps in Chapter 5.&rdquo;"
        ),
    ]


def make_section_cheatsheet():
    return [
        H1("16. One-page cheat sheet"),
        P(
            "Print this page. Memorize these answers. They cover the questions you "
            "are most likely to be asked in the first three minutes of any "
            "discussion of the chapter."
        ),
        H2("Numbers to remember exactly"),
        *Bullets([
            "<b>5,410</b> = test set size (20% of 27,050).",
            "<b>14</b> = career categories.",
            "<b>29</b> = features per row.",
            "<b>30</b> = questionnaire items.",
            "<b>3</b> = recommendations shown to the user.",
            "<b>99.8%</b> top-1 accuracy.",
            "<b>99.9%</b> top-3 accuracy.",
            "<b>0.998</b> macro-F1.",
            "<b>0.9995 / 0.9996</b> micro / macro AUC (one-vs-rest).",
            "<b>ECE &asymp; 0.0002</b>, Brier &asymp; 0.0027.",
            "<b>9</b> total misclassifications.",
            "<b>4</b> Education&rarr;Medicine, <b>4</b> scattered CS&amp;T errors, <b>1</b> Arts&rarr;Education.",
            "<b>86.7%</b> top-3 hit rate in the employee validation (N=30 convenience sample).",
        ]),
        H2("One-liners by topic"),
        *Bullets([
            "<b>Why three recommendations?</b> Cheap safety margin; covers borderline "
            "cases without overwhelming the user.",
            "<b>Why isotonic calibration?</b> Free post-hoc fix on a held-out slice, "
            "more flexible than Platt for tree models, makes the confidence percentages "
            "honest.",
            "<b>Why XGBoost over LightGBM?</b> Higher 5-fold stratified top-3 accuracy "
            "during tuning.",
            "<b>Why baselines?</b> If the fancy model doesn&rsquo;t beat them, the "
            "&lsquo;fanciness&rsquo; was free. Random &asymp; 7%, majority &asymp; 13% "
            "&mdash; both as expected, so the test is fair.",
            "<b>Why so easy?</b> Because the engineered feature space (29 numeric "
            "predictors) already separates 14 broad categories well. Logistic "
            "regression confirms this.",
            "<b>Why this is not real-world proof:</b> training labels are from adult "
            "career corpora; the questionnaire-to-feature mapping is not graded here; "
            "leakage audits are still to do; the deployment audience is SHS students.",
        ]),
    ]


def make_section_questions():
    items = [
        (
            "1. Why is your top-1 accuracy 99.8%? Isn&rsquo;t that suspicious?",
            "It is high because the merged dataset is already largely separable in "
            "the 29-feature space. We back this up by showing that a simple "
            "multinomial logistic regression also reaches 99.3% on the same split, "
            "so the task is intrinsically easy here — the boosting model only "
            "refines the few hard cases. We are transparent that this is an internal "
            "engineering sanity check, not a real-world prediction guarantee, and we "
            "list the leakage and ablation audits we still owe.",
        ),
        (
            "2. Why use XGBoost if logistic regression already hits 99.3%?",
            "Three reasons. First, XGBoost gives a small but real improvement on the "
            "few borderline cases. Second, gradient-boosted trees handle non-linear "
            "interactions between features (e.g. high R-score AND low S-score together) "
            "more naturally if data ever becomes harder. Third, XGBoost cleanly "
            "supports post-hoc isotonic calibration via "
            "CalibratedClassifierCV on a held-out slice, which is essential because "
            "we show probabilities to users.",
        ),
        (
            "3. Why do you display three recommendations instead of one?",
            "Because the system is decision support, not a placement tool. Showing the "
            "top three gives a low-cost safety margin: even when the model is slightly "
            "unsure about a profile, the correct field is almost always in the top "
            "three. The methodology choice is also reflected in the tuning objective "
            "— we optimised cross-validated top-3 accuracy.",
        ),
        (
            "4. What is calibration and why did you bother with it?",
            "Calibration is whether the probability the model displays actually matches "
            "how often it is right. If we show &lsquo;85% likely&rsquo; on many cases, "
            "ideally about 85% of them really are correct. Without calibration, an "
            "over-confident model could lead users to trust recommendations they "
            "shouldn&rsquo;t. We applied isotonic regression on a 15% held-out slice "
            "and got ECE &asymp; 0.0002 and Brier &asymp; 0.0027, well below our 0.10 "
            "ECE target.",
        ),
        (
            "5. What does ECE = 0.0002 actually mean?",
            "It means that, on average across confidence bins, the gap between the "
            "predicted probability and the empirical accuracy is about 0.02 percentage "
            "points. In plain words: when the system says 90% sure, it really is "
            "about 90% accurate on those cases. The metric is computed on the "
            "top-1 confidence using the same 5,410-row holdout.",
        ),
        (
            "6. Where do your 9 mistakes come from?",
            "They form a pattern, not noise. Four are Education &rarr; Medicine: both "
            "involve working with people AND a science/investigation dimension, so they "
            "look similar in feature space. Four are scattered out of Computer Science "
            "&amp; Technology, which is the biggest class (700 rows in the holdout) so "
            "it has more borderline profiles. One is Arts &rarr; Education. We would "
            "fix these by adding questionnaire items that sharpen the "
            "&lsquo;people&rsquo; and &lsquo;health&rsquo; signals, not by tuning "
            "the model further.",
        ),
        (
            "7. Why include t-SNE if you cannot trust its distances?",
            "Because it gives readers a quick visual intuition for whether the 14 "
            "career categories form recognisable clusters in feature space. It is a "
            "visualization tool, not a metric. We explicitly say in the discussion "
            "that the actual evidence for separability comes from the confusion "
            "matrix, calibration curve, and per-class F1, not from the t-SNE map.",
        ),
        (
            "8. What is information leakage and how could it affect your results?",
            "Information leakage is when training-time information accidentally "
            "duplicates test-time information — e.g. near-duplicate rows on both "
            "sides of the split, or synthetic rows generated by the same rules that "
            "create the labels. It can make accuracy look great while masking that the "
            "model is just remembering. We address this honestly by reporting the "
            "specific audits that are still to do: duplicate detection, source-wise "
            "splits, and feature-family ablations.",
        ),
        (
            "9. Why are macro-F1, weighted-F1, and accuracy all almost the same here?",
            "Because the classes are roughly balanced after downsampling (max 3,500 "
            "for the biggest class, 1,800 for most others) and accuracy is near "
            "perfect across every class. When every class is healthy, macro-F1 and "
            "weighted-F1 converge to the same number. If one class quietly collapsed, "
            "macro-F1 would drop faster than weighted-F1 — that is exactly why "
            "we report macro.",
        ),
        (
            "10. What did the employee validation prove?",
            "It is a supplementary face-validity check, not a validation study. 30 "
            "working professionals from a convenience sample took the live "
            "questionnaire and self-reported whether their actual field was in the "
            "top 3. 86.7% (26 of 30) said yes. That is directional evidence that the "
            "deployed pipeline produces plausible outputs when real adults use it. It "
            "does NOT prove correctness for SHS students; that requires a separate "
            "study with counselor-rated outcomes.",
        ),
        (
            "11. Why is your top-3 higher than your top-1?",
            "Mathematically, top-k is non-decreasing in k. The cases where the model "
            "is slightly uncertain about a profile still usually have the correct "
            "answer as second or third choice. So widening the answer from one to "
            "three guesses catches almost all of the remaining hard cases. That is "
            "also why we tuned hyperparameters on cross-validated top-3 accuracy.",
        ),
        (
            "12. Why didn&rsquo;t you evaluate the questionnaire-to-feature mapping?",
            "Because that would require a separately labelled sample — ideally "
            "SHS students with verified career outcomes — and that sample does "
            "not exist yet. Chapter 4 evaluates the CLASSIFIER on already-prepared "
            "tabular rows. The mapping is a fixed heuristic. Evaluating it is "
            "explicitly listed as future work, alongside counselor-rated relevance "
            "and student-rated usefulness as proxy criteria.",
        ),
        (
            "13. Could your model be biased toward common careers like Computer Science?",
            "It could in principle, which is why we (a) downsampled CS&amp;T to a cap "
            "of 3,500 rows before splitting, (b) report macro-F1 and macro-AUC so big "
            "classes can&rsquo;t hide weaker classes, and (c) inspect per-class "
            "precision and recall. CS&amp;T does have slightly lower recall (~0.994) "
            "exactly because it&rsquo;s the largest and most varied class — not "
            "because of class imbalance favouring it. Future fairness audits should "
            "also disaggregate by sex and region when those fields are ethically "
            "collectable.",
        ),
        (
            "14. What is dataset shift and how does it apply here?",
            "Dataset shift is when the joint distribution of features and labels in "
            "training differs from deployment. Here, training labels come from adult "
            "career corpora, while the deployment target is SHS students. Even with "
            "the same 29-feature schema, the meaning of those features for a 16-year-"
            "old who is still exploring differs from an adult who has settled into a "
            "field. This is the central reason we frame the work as a prototype, "
            "monitor for drift after deployment, and require external validation "
            "before claiming SHS-facing predictive accuracy.",
        ),
        (
            "15. How would you make this evaluation stronger?",
            "Three concrete steps. (1) Internal robustness: run duplicate audits, "
            "source-wise / grouped splits, and feature-family ablations to show the "
            "model isn&rsquo;t leaning on accidental signals. (2) SHS pilot: run a "
            "study with SHS respondents under ethics clearance, using counselor-"
            "rated relevance and student-rated usefulness as proxy outcomes, plus "
            "alignment with stated strand or tertiary plans. (3) Longitudinal "
            "follow-up: revisit participants after enough time has passed to "
            "compare recommendations against actual career trajectories. These are "
            "exactly the staged recommendations in Chapter 5.",
        ),
    ]
    out = [
        H1("17. Top 15 likely defense questions"),
        P(
            "Practice saying these answers out loud. The exact wording doesn&rsquo;t "
            "have to match — but the SHAPE of each answer (claim &rarr; evidence "
            "&rarr; honest caveat) should."
        ),
    ]
    for q, a in items:
        out.append(Q(q))
        out.append(A(a))
    return out


if __name__ == "__main__":
    build_pdf()
