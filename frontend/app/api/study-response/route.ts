import { NextRequest, NextResponse } from "next/server";
import { appendFileSync, existsSync, mkdirSync } from "fs";
import { join } from "path";

/**
 * Persists validation-study rows to repo data/ (same cwd convention as /api/predict).
 * Not suitable for read-only or ephemeral serverless disks — use a DB or blob store in production.
 */
const CSV_FILENAME = "employee_validation_sessions.csv";

function escapeCsvField(value: string | number | boolean | null | undefined): string {
  if (value === null || value === undefined) return "";
  const s = typeof value === "string" ? value : String(value);
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

function rowFromPayload(p: Record<string, string | number | boolean>): string {
  const header = [
    "submitted_at_utc",
    "session_id",
    "consent_version",
    "consent_timestamp",
    "participant_name",
    "tenure_total_months",
    "tenure_years_part",
    "tenure_months_part",
    "job_satisfaction",
    "self_reported_career_field",
    "job_title",
    "total_work_experience_years",
    "education_level",
    "responses_json",
    "pred_career_1",
    "pred_prob_1",
    "pred_career_2",
    "pred_prob_2",
    "pred_career_3",
    "pred_prob_3",
    "computed_self_reported_in_top3",
    "participant_field_in_top3_answer",
    "rating_top1",
    "rating_top2",
    "rating_top3",
  ];

  const values = header.map((key) => {
    const v = p[key];
    return escapeCsvField(v);
  });
  return values.join(",") + "\n";
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const sessionId = typeof body.sessionId === "string" ? body.sessionId.trim() : "";
    if (!sessionId) {
      return NextResponse.json({ error: "sessionId is required." }, { status: 400 });
    }

    const screening = body.screening;
    if (!screening || typeof screening !== "object") {
      return NextResponse.json({ error: "screening object is required." }, { status: 400 });
    }

    const name = typeof screening.participantName === "string" ? screening.participantName.trim() : "";
    if (!name) {
      return NextResponse.json({ error: "screening.participantName is required." }, { status: 400 });
    }

    const totalMonths = Number(screening.totalMonthsTenure);
    if (!Number.isFinite(totalMonths) || totalMonths <= 0) {
      return NextResponse.json({ error: "Invalid tenure." }, { status: 400 });
    }

    const sat = Number(screening.jobSatisfaction);
    if (!Number.isInteger(sat) || sat < 1 || sat > 5) {
      return NextResponse.json({ error: "Invalid job satisfaction." }, { status: 400 });
    }

    const field =
      typeof screening.selfReportedCareerField === "string" ? screening.selfReportedCareerField.trim() : "";

    const responses = body.questionnaireResponses;
    if (!Array.isArray(responses) || responses.length !== 30) {
      return NextResponse.json({ error: "questionnaireResponses must be an array of length 30." }, { status: 400 });
    }

    const predictions = body.predictions;
    if (!Array.isArray(predictions) || predictions.length < 3) {
      return NextResponse.json({ error: "predictions must have at least 3 entries." }, { status: 400 });
    }

    const fieldInTop3 = body.fieldInTop3;
    if (fieldInTop3 !== "yes" && fieldInTop3 !== "no" && fieldInTop3 !== "not_sure") {
      return NextResponse.json({ error: "fieldInTop3 must be yes, no, or not_sure." }, { status: 400 });
    }

    const computed =
      typeof body.computedSelfReportedInTop3 === "boolean" ? body.computedSelfReportedInTop3 : false;

    const r1 = body.ratingTop1;
    const r2 = body.ratingTop2;
    const r3 = body.ratingTop3;
    const needRatings = fieldInTop3 === "no" || fieldInTop3 === "not_sure";
    if (needRatings) {
      for (const [i, r] of [r1, r2, r3].entries()) {
        const n = Number(r);
        if (!Number.isInteger(n) || n < 1 || n > 5) {
          return NextResponse.json(
            { error: `ratingTop${i + 1} must be an integer 1–5 when fieldInTop3 is no or not_sure.` },
            { status: 400 }
          );
        }
      }
    }

    const submittedAt = typeof body.feedbackSubmittedAt === "string" ? body.feedbackSubmittedAt : new Date().toISOString();
    const consentVersion = typeof body.consentVersion === "string" ? body.consentVersion : "";
    const consentTimestamp = typeof body.consentTimestamp === "string" ? body.consentTimestamp : "";

    const top = predictions.slice(0, 3) as { career?: string; probability?: number }[];
    const responsesJson = JSON.stringify(responses);

    const row: Record<string, string | number | boolean> = {
      submitted_at_utc: submittedAt,
      session_id: sessionId,
      consent_version: consentVersion,
      consent_timestamp: consentTimestamp,
      participant_name: name,
      tenure_total_months: totalMonths,
      tenure_years_part: Number(screening.tenureYears) || 0,
      tenure_months_part: Number(screening.tenureMonths) || 0,
      job_satisfaction: sat,
      self_reported_career_field: field,
      job_title:
        typeof screening.jobTitle === "string" && screening.jobTitle.trim()
          ? screening.jobTitle.trim()
          : "",
      total_work_experience_years:
        screening.totalWorkExperienceYears != null && String(screening.totalWorkExperienceYears).trim() !== ""
          ? String(screening.totalWorkExperienceYears).trim()
          : "",
      education_level:
        typeof screening.educationLevel === "string" && screening.educationLevel.trim()
          ? screening.educationLevel.trim()
          : "",
      responses_json: responsesJson,
      pred_career_1: top[0]?.career ?? "",
      pred_prob_1: top[0]?.probability ?? "",
      pred_career_2: top[1]?.career ?? "",
      pred_prob_2: top[1]?.probability ?? "",
      pred_career_3: top[2]?.career ?? "",
      pred_prob_3: top[2]?.probability ?? "",
      computed_self_reported_in_top3: computed,
      participant_field_in_top3_answer: fieldInTop3,
      rating_top1: needRatings ? Number(r1) : "",
      rating_top2: needRatings ? Number(r2) : "",
      rating_top3: needRatings ? Number(r3) : "",
    };

    const projectRoot = join(process.cwd(), "..");
    const dataDir = join(projectRoot, "data");
    const csvPath = join(dataDir, CSV_FILENAME);

    if (!existsSync(dataDir)) {
      mkdirSync(dataDir, { recursive: true });
    }

    const headerLine =
      "submitted_at_utc,session_id,consent_version,consent_timestamp,participant_name,tenure_total_months,tenure_years_part,tenure_months_part,job_satisfaction,self_reported_career_field,job_title,total_work_experience_years,education_level,responses_json,pred_career_1,pred_prob_1,pred_career_2,pred_prob_2,pred_career_3,pred_prob_3,computed_self_reported_in_top3,participant_field_in_top3_answer,rating_top1,rating_top2,rating_top3\n";

    if (!existsSync(csvPath)) {
      appendFileSync(csvPath, headerLine, "utf8");
    }

    appendFileSync(csvPath, rowFromPayload(row), "utf8");

    return NextResponse.json({ ok: true });
  } catch (e) {
    console.error("study-response:", e);
    return NextResponse.json({ error: "Failed to save response." }, { status: 500 });
  }
}
