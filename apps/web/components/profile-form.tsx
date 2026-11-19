"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { apiErrorMessage } from "@/lib/api-error";

type ProfileFormProps = {
  initialName: string;
  initialTimezone: string;
  email: string;
};

export function ProfileForm({ initialName, initialTimezone, email }: ProfileFormProps) {
  const router = useRouter();
  const errorRef = useRef<HTMLParagraphElement>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setPending(true);

    const data = new FormData(event.currentTarget);

    try {
      const response = await fetch("/api/account/profile", {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          name: String(data.get("name") ?? ""),
          timezone: String(data.get("timezone") ?? ""),
        }),
      });
      const body = await response.json().catch(() => null);

      if (!response.ok) {
        setError(apiErrorMessage(body));
        requestAnimationFrame(() => errorRef.current?.focus());
        return;
      }

      setMessage("Профиль сохранён.");
      router.refresh();
    } catch {
      setError("Сервис временно недоступен. Попробуйте ещё раз.");
      requestAnimationFrame(() => errorRef.current?.focus());
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="form form-wide" method="post" onSubmit={handleSubmit}>
      {error ? (
        <p className="form-error" role="alert" tabIndex={-1} ref={errorRef}>
          {error}
        </p>
      ) : null}

      {message ? (
        <p className="form-notice" role="status">
          {message}
        </p>
      ) : null}

      <div className="field">
        <span className="field-label">Email</span>
        <p className="field-static">{email}</p>
        <p className="field-hint">Email пока нельзя изменить самостоятельно.</p>
      </div>

      <div className="field">
        <label htmlFor="name">Имя</label>
        <input
          id="name"
          name="name"
          type="text"
          autoComplete="name"
          maxLength={120}
          defaultValue={initialName}
          required
        />
      </div>

      <div className="field">
        <label htmlFor="timezone">Часовой пояс</label>
        <input
          id="timezone"
          name="timezone"
          type="text"
          autoComplete="off"
          autoCapitalize="none"
          spellCheck={false}
          defaultValue={initialTimezone}
          required
        />
        <p className="field-hint">
          Формат IANA, например <code>Europe/Moscow</code> или <code>Asia/Tbilisi</code>.
          Нужен для расписания занятий.
        </p>
      </div>

      <button className="button form-submit" type="submit" disabled={pending}>
        {pending ? "Сохраняем…" : "Сохранить"}
      </button>
    </form>
  );
}
