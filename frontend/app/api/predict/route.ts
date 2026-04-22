import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import { join } from "path";
import { existsSync } from "fs";

function messageFromUpstreamJson(data: unknown): string {
  if (typeof data !== "object" || data === null) {
    return "Prediction service returned an invalid response.";
  }
  const o = data as Record<string, unknown>;
  if (typeof o.error === "string") return o.error;
  const detail = o.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return JSON.stringify(detail);
  return "Prediction service request failed.";
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { responses } = body;

    if (!responses || !Array.isArray(responses)) {
      return NextResponse.json(
        { error: "Invalid request. 'responses' array is required." },
        { status: 400 }
      );
    }

    if (responses.length !== 30) {
      return NextResponse.json(
        { error: "Exactly 30 responses are required." },
        { status: 400 }
      );
    }

    const predictUrl = process.env.PREDICT_API_URL?.trim();

    if (predictUrl) {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      const apiKey = process.env.PREDICT_API_KEY?.trim();
      if (apiKey) {
        headers["X-Api-Key"] = apiKey;
      }

      const upstream = await fetch(predictUrl, {
        method: "POST",
        headers,
        body: JSON.stringify({ responses }),
      });

      const rawText = await upstream.text();
      let parsed: unknown;
      try {
        parsed = rawText ? JSON.parse(rawText) : null;
      } catch {
        return NextResponse.json(
          { error: "Prediction service returned non-JSON." },
          { status: 502 }
        );
      }

      if (!upstream.ok) {
        return NextResponse.json(
          { error: messageFromUpstreamJson(parsed) },
          { status: upstream.status >= 400 && upstream.status < 600 ? upstream.status : 502 }
        );
      }

      if (
        typeof parsed !== "object" ||
        parsed === null ||
        !("predictions" in parsed) ||
        !Array.isArray((parsed as { predictions: unknown }).predictions)
      ) {
        return NextResponse.json(
          { error: "Prediction service response missing predictions." },
          { status: 502 }
        );
      }

      return NextResponse.json(parsed as { predictions: unknown[] });
    }

    // Local dev: call repo-root Python script (see README).
    const projectRoot = join(process.cwd(), "..");
    const pythonScript = join(projectRoot, "api", "predict.py");

    const venvPythonWindows = join(projectRoot, "venv", "Scripts", "python.exe");
    const venvPythonUnix = join(projectRoot, "venv", "bin", "python");
    const venvPython3Unix = join(projectRoot, "venv", "bin", "python3");

    let pythonExecutable: string;
    if (existsSync(venvPythonWindows)) {
      pythonExecutable = venvPythonWindows;
    } else if (existsSync(venvPythonUnix)) {
      pythonExecutable = venvPythonUnix;
    } else if (existsSync(venvPython3Unix)) {
      pythonExecutable = venvPython3Unix;
    } else {
      pythonExecutable = "python3";
    }

    const pythonProcess = spawn(pythonExecutable, [pythonScript], {
      cwd: projectRoot,
    });

    let stdout = "";
    let stderr = "";

    pythonProcess.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    pythonProcess.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    pythonProcess.stdin.write(JSON.stringify({ responses }));
    pythonProcess.stdin.end();

    await new Promise<void>((resolve, reject) => {
      pythonProcess.on("close", (code) => {
        if (code !== 0) {
          reject(new Error(`Python script failed: ${stderr}`));
        } else {
          resolve();
        }
      });
    });

    const result = JSON.parse(stdout) as { error?: string; predictions?: unknown[] };

    if (result.error) {
      return NextResponse.json({ error: result.error }, { status: 500 });
    }

    return NextResponse.json(result);
  } catch (error: unknown) {
    console.error("Prediction error:", error);
    const message =
      error instanceof Error ? error.message : "Internal server error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
