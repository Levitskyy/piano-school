"use client";

import Link from "next/link";
import { useRef, useState } from "react";

import { apiErrorMessage } from "@/lib/api-error";

export function ForgotPasswordForm() {
  const errorRef = useRef<HTMLParagraphElement>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [devResetUrl, setDevResetUrl] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setDevResetUrl(null);
    setPending(true);

    const data = new FormData(event.currentTarget);

    try {
      const response = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email: String(data.get("email") ?? "") }),
      });
      const body = await response.json().catch(() => null);

      if (!response.ok) {
        setError(apiErrorMessage(body));
        requestAnimationFrame(() => errorRef.current?.focus());
        return;
      }

      setMessage(
        body?.message ??
          "Если аккаунт существует, мы отправили ссылку для восстановления.",
      );
      setDevResetUrl(body?.dev_reset_url ?? null);
    } catch {
      setError("Сервис временно недоступен. Попробуйте ещё раз.");
      requestAnimationFrame(() => errorRef.current?.focus());
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="form" method="post" onSubmit={handleSubmit} aria-labelledby="main-heading">
      {error ? (
        <p className="form-error" role="alert" tabIndex={-1} ref={errorRef}>
          {error}
        </p>
      ) : null}

      {message ? (
        <div className="form-notice" role="status">
          <p>{message}</p>
          {devResetUrl ? (
            <p>
              Локальный режим:{" "}
              <Link href={devResetUrl}>открыть ссылку для сброса пароля</Link>.
            </p>
          ) : null}
        </div>
      ) : null}

      <div className="field">
        <label htmlFor="email">Email</label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="username"
          autoCapitalize="none"
          spellCheck={false}
          required
        />
      </div>

      <button className="button form-submit" type="submit" disabled={pending}>
        {pending ? "Отправляем…" : "Отправить ссылку"}
      </button>

      <p className="form-switch">
        <Link href="/login">← Вернуться ко входу</Link>
      </p>
    </form>
  );
}
