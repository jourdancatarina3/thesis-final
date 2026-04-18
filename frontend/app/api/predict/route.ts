import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import { join } from "path";
import { existsSync } from "fs";

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

    // Validate responses
    if (responses.length !== 30) {
      return NextResponse.json(
        { error: "Exactly 30 responses are required." },
        { status: 400 }
      );
    }

    // Call Python prediction script
    // Path relative to project root (one level up from frontend)
    const projectRoot = join(process.cwd(), "..");
    const pythonScript = join(projectRoot, "api", "predict.py");
    
    // Use Python from venv if available, otherwise use system Python
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
      // Try python3 first (common on macOS), then fallback to python
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

    // Send input to Python script
    pythonProcess.stdin.write(JSON.stringify({ responses }));
    pythonProcess.stdin.end();

    // Wait for process to complete
    await new Promise<void>((resolve, reject) => {
      pythonProcess.on("close", (code) => {
        if (code !== 0) {
          reject(new Error(`Python script failed: ${stderr}`));
        } else {
          resolve();
        }
      });
    });

    // Parse output
    const result = JSON.parse(stdout);

    if (result.error) {
      return NextResponse.json(
        { error: result.error },
        { status: 500 }
      );
    }

    return NextResponse.json(result);
  } catch (error: any) {
    console.error("Prediction error:", error);
    return NextResponse.json(
      { error: error.message || "Internal server error" },
      { status: 500 }
    );
  }
}
