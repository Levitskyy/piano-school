"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiErrorMessage } from "@/lib/api-error";
import { formatSlotDateTime } from "@/lib/individual-lessons-shared";

type LessonBookingActionsProps = {
  bookingId: string;
  startsAt: string;
  canChange: boolean;
  timeZone: string;
};

export function LessonBookingActions({
  bookingId,
  startsAt,
  canChange,
  timeZone,
}: LessonBookingActionsProps) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!canChange) {
    return (
      <p className="booking-note">
        Изменить или отменить занятие уже нельзя. Напишите преподавателю.
      </p>
    );
  }

  async function handleCancel() {
    const label = formatSlotDateTime(startsAt, timeZone);
    if (
      !window.confirm(
        `Отменить занятие ${label}? Урок вернётся в пакет, и вы сможете выбрать другое время.`,
      )
    ) {
      return;
    }

    setPending(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/individual-lessons/bookings/${bookingId}/cancel`,
        { method: "POST" },
      );
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        setError(apiErrorMessage(payload));
        return;
      }
      router.refresh();
    } catch {
      setError("Сервис временно недоступен. Попробуйте ещё раз.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="booking-actions-row">
      <Link
        className="button button-small button-ghost"
        href={`/account/individual-lessons/bookings/${bookingId}/reschedule`}
      >
        Перенести
      </Link>
      <button
        className="button button-small button-ghost"
        type="button"
        disabled={pending}
        onClick={() => void handleCancel()}
      >
        {pending ? "Отменяем…" : "Отменить"}
      </button>
      {error ? (
        <p className="form-error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
