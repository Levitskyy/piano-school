"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiErrorMessage } from "@/lib/api-error";

type LessonProgressProps = {
  courseSlug: string;
  lessonSlug: string;
  initialStatus: string;
};

export function LessonProgress({
  courseSlug,
  lessonSlug,
  initialStatus,
}: LessonProgressProps) {
  const router = useRouter();
  const [status, setStatus] = useState(initialStatus);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const completed = status === "completed";

  async function updateStatus(nextStatus: "in_progress" | "completed") {
    setPending(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/courses/${encodeURIComponent(courseSlug)}/lessons/${encodeURIComponent(
          lessonSlug,
        )}/progress`,
        {
          method: "PATCH",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            status: nextStatus,
            last_position_seconds: 0,
          }),
        },
      );

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        setError(apiErrorMessage(body));
        return;
      }

      setStatus(nextStatus);
      router.refresh();
    } catch {
      setError("Не удалось сохранить прогресс. Попробуйте ещё раз.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="lesson-progress">
      <div>
        <p className="eyebrow">Прогресс</p>
        <p aria-live="polite">
          {completed ? "Урок отмечен как завершённый." : "Урок ещё в работе."}
        </p>
        {error ? (
          <p className="form-error" role="alert">
            {error}
          </p>
        ) : null}
      </div>

      <button
        className={completed ? "button button-ghost" : "button"}
        type="button"
        onClick={() => updateStatus(completed ? "in_progress" : "completed")}
        disabled={pending}
      >
        {pending
          ? "Сохраняем…"
          : completed
            ? "Вернуть в работу"
            : "Отметить завершённым"}
      </button>
    </div>
  );
}
