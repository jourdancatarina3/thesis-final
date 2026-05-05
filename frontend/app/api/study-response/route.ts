import { NextRequest, NextResponse } from "next/server";
import { isTenureBandId, tenureBandToParts } from "@/lib/studySession";
import { createSupabaseAdmin } from "@/lib/supabaseAdmin";

function isUniqueViolation(error: { code?: string; message?: string } | null): boolean {
  if (!error) return false;
  if (error.code === "23505") return true;
  return typeof error.message === "string" && error.message.toLowerCase().includes("duplicate");
}

export async function POST(request: NextRequest) {
  const supabase = createSupabaseAdmin();
  if (!supabase) {
    return NextResponse.json(
      {
        error:
          "Study data storage is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY on the server.",
      },
      { status: 503 }
    );
  }

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

    const name =
      typeof screening.participantName === "string" ? screening.participantName.trim() : "";

    const bandRaw = typeof screening.tenureBand === "string" ? screening.tenureBand.trim() : "";
    if (!isTenureBandId(bandRaw)) {
      return NextResponse.json({ error: "Invalid or missing tenureBand." }, { status: 400 });
    }
    const { tenureYears, tenureMonths, totalMonthsTenure: totalMonths } = tenureBandToParts(bandRaw);

    const sat = Number(screening.jobSatisfaction);
    if (!Number.isInteger(sat) || sat < 1 || sat > 5) {
      return NextResponse.json({ error: "Invalid job satisfaction." }, { status: 400 });
    }

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

    const consentVersion = typeof body.consentVersion === "string" ? body.consentVersion : "";

    const top = predictions.slice(0, 3) as { career?: string; probability?: number }[];

    const insertRow = {
      session_id: sessionId,
      consent_version: consentVersion,
      participant_name: name,
      tenure_band: bandRaw,
      tenure_total_months: totalMonths,
      tenure_years_part: tenureYears,
      tenure_months_part: tenureMonths,
      job_satisfaction: sat,
      responses_json: responses,
      pred_career_1: top[0]?.career ?? "",
      pred_prob_1: typeof top[0]?.probability === "number" ? top[0].probability : null,
      pred_career_2: top[1]?.career ?? "",
      pred_prob_2: typeof top[1]?.probability === "number" ? top[1].probability : null,
      pred_career_3: top[2]?.career ?? "",
      pred_prob_3: typeof top[2]?.probability === "number" ? top[2].probability : null,
      computed_self_reported_in_top3: computed,
      participant_field_in_top3_answer: fieldInTop3,
    };

    const { error } = await supabase.from("employee_validation_sessions").insert(insertRow);

    if (error) {
      if (isUniqueViolation(error)) {
        return NextResponse.json(
          { error: "This session was already submitted. Duplicate responses were not saved." },
          { status: 409 }
        );
      }
      console.error("study-response supabase:", error);
      return NextResponse.json({ error: "Failed to save response." }, { status: 500 });
    }

    return NextResponse.json({ ok: true });
  } catch (e) {
    console.error("study-response:", e);
    return NextResponse.json({ error: "Failed to save response." }, { status: 500 });
  }
}
