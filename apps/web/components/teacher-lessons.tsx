"use client";

import { useRouter } from "next/navigation";
import { useId, useRef, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { apiErrorMessage } from "@/lib/api-error";
import { formatSlotDateTime } from "@/lib/individual-lessons-shared";
import type { TeacherLessonBooking } from "@/lib/teacher";

const statusLabels: Record<string, string> = {
  confirmed: "подтверждено",
  completed: "проведено",
  cancelled: "отменено",
};

type TeacherLessonBookingListProps = {
  bookings: TeacherLessonBooking[];
  timeZone: string;
  emptyTitle: string;
  emptyText: string;
};

function BookingCard({
  booking,
  timeZone,
}: {
  booking: TeacherLessonBooking;
  timeZone: string;
}) {
  const router = useRouter();
  const inputId = useId();
  const errorRef = useRef<HTMLParagraphElement>(null);
  const [meetingUrl, setMeetingUrl] = useState(booking.meeting_url ?? "");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSaved(false);
    setPending(true);

    try {
      const response = await fetch(`/api/teacher/lessons/${booking.id}`, {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ meeting_url: meetingUrl.trim() || null }),
      });
      const body = await response.json().catch(() => null);

      if (!response.ok) {
        setError(apiErrorMessage(body));
        requestAnimationFrame(() => errorRef.current?.focus());
        return;
      }

      setSaved(true);
      router.refresh();
    } catch {
      setError("Сервис временно недоступен. Попробуйте ещё раз.");
      requestAnimationFrame(() => errorRef.current?.focus());
    } finally {
      setPending(false);
    }
  }

  return (
    <li className="teacher-booking-card">
      <div className="teacher-booking-head">
        <div>
          <h3>{booking.offer_title}</h3>
          <p className="teacher-booking-student">
            {booking.student_name} · {booking.student_email}
          </p>
        </div>
        <span className="status-pill">
          {statusLabels[booking.status] ?? booking.status}
        </span>
      </div>

      <p className="teacher-booking-time">
        {formatSlotDateTime(booking.starts_at, timeZone)}
      </p>

      {booking.meeting_url ? (
        <p>
          <a href={booking.meeting_url} target="_blank" rel="noreferrer">
            Открыть ссылку на встречу
          </a>
        </p>
      ) : null}

      <form className="meeting-form" onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor={inputId}>Ссылка на встречу</label>
          <input
            id={inputId}
            name="meeting_url"
            type="url"
            inputMode="url"
            placeholder="https://..."
            value={meetingUrl}
            onChange={(event) => {
              setMeetingUrl(event.target.value);
              setSaved(false);
            }}
          />
        </div>
        <button className="button button-small" type="submit" disabled={pending}>
          {pending ? "Сохраняем…" : "Сохранить"}
        </button>
      </form>

      {error ? (
        <p className="form-error" role="alert" tabIndex={-1} ref={errorRef}>
          {error}
        </p>
      ) : null}
      {saved ? (
        <p className="form-notice" role="status">
          Ссылка сохранена.
        </p>
      ) : null}
    </li>
  );
}

export function TeacherLessonBookingList({
  bookings,
  timeZone,
  emptyTitle,
  emptyText,
}: TeacherLessonBookingListProps) {
  if (bookings.length === 0) {
    return <EmptyState title={emptyTitle} text={emptyText} />;
  }

  return (
    <ul className="teacher-booking-list">
      {bookings.map((booking) => (
        <BookingCard
          booking={booking}
          key={`${booking.id}-${booking.meeting_url ?? "empty"}`}
          timeZone={timeZone}
        />
      ))}
    </ul>
  );
}
