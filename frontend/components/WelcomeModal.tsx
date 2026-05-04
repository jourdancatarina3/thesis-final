"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const SESSION_KEY = "home_welcome_modal_seen";

export default function WelcomeModal() {
  const [open, setOpen] = useState(false);
  const continueRef = useRef<HTMLButtonElement>(null);

  const dismiss = useCallback(() => {
    try {
      sessionStorage.setItem(SESSION_KEY, "1");
    } catch {
      /* ignore */
    }
    setOpen(false);
  }, []);

  useEffect(() => {
    try {
      if (sessionStorage.getItem(SESSION_KEY)) return;
    } catch {
      /* ignore */
    }
    setOpen(true);
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") dismiss();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    queueMicrotask(() => continueRef.current?.focus());
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, dismiss]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/50 p-4 pb-8 backdrop-blur-sm sm:items-center sm:pb-4"
      role="presentation"
      onClick={dismiss}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="welcome-modal-title"
        aria-describedby="welcome-modal-desc"
        className="relative w-full max-w-lg rounded-2xl border border-white/20 bg-white p-6 shadow-2xl sm:p-8"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 inline-flex rounded-full bg-gradient-to-r from-blue-100 to-indigo-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-indigo-800">
          Welcome
        </div>
        <h2
          id="welcome-modal-title"
          className="text-xl font-bold leading-tight text-gray-900 sm:text-2xl"
        >
          Wondering if you&apos;re in the right career, or what else might fit?
        </h2>
        <div id="welcome-modal-desc" className="mt-4 space-y-3 text-sm leading-relaxed text-gray-600 sm:text-base">
          <p>
            A short, reflective questionnaire turns your preferences and work style into a map of
            college-field directions that line up with who you are, not just your job title today.
          </p>
          <p>
            You&apos;ll get a moment to see how strongly your path matches those ideas, and which
            other fields might deserve a closer look, all based on your own answers.
          </p>
          <p className="text-xs text-gray-500 sm:text-sm">
            You&apos;re also helping validate thesis research; your responses are handled as
            described in the consent form when you begin.
          </p>
        </div>
        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:justify-end">
          <button
            type="button"
            onClick={dismiss}
            className="order-2 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm font-semibold text-gray-700 shadow-sm transition hover:bg-gray-50 sm:order-1"
          >
            Maybe later
          </button>
          <button
            ref={continueRef}
            type="button"
            onClick={dismiss}
            className="order-1 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-5 py-3 text-sm font-semibold text-white shadow-lg transition hover:from-blue-700 hover:to-indigo-700 hover:shadow-xl sm:order-2"
          >
            Continue to the study
          </button>
        </div>
      </div>
    </div>
  );
}
