"use client";

import Link from "next/link";
import { useId, useRef, useState } from "react";

import { apiErrorMessage } from "@/lib/api-error";

export function ResetPasswordForm({ token }: { token: string }) {
  const hintId = useId();
  const errorRef = useRef<HTMLParagraphElement>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const data = new FormData(event.currentTarget);
    const password = String(data.get("password") ?? "");
    const confirmation = String(data.get("confirmation") ?? "");

    if (password !== confirmation) {
      setError("Пароли не совпадают.");
      requestAnimationFrame(() => errorRef.current?.focus());
      return;
    }

    setPending(true);
    try {
      const response = await fetch("/api/auth/reset-password", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });
      const body = await response.json().catch(() => null);

      if (!response.ok) {
        setError(apiErrorMessage(body));
        requestAnimationFrame(() => errorRef.current?.focus());
        return;
      }

      setDone(true);
    } catch {
      setError("Сервис временно недоступен. Попробуйте ещё раз.");
      requestAnimationFrame(() => errorRef.current?.focus());
    } finally {
      setPending(false);
    }
  }

  if (done) {
    return (
      <div className="form-notice" role="status">
        <p>Пароль обновлён.</p>
        <p>
          <Link href="/login">Войти с новым паролем</Link>
        </p>
      </div>
    );
  }

  return (
    <form className="form" method="post" onSubmit={handleSubmit} aria-labelledby="main-heading">
      {error ? (
        <p className="form-error" role="alert" tabIndex={-1} ref={errorRef}>
          {error}
        </p>
      ) : null}

      <div className="field">
        <label htmlFor="password">Новый пароль</label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="new-password"
          minLength={8}
          maxLength={128}
          aria-describedby={hintId}
          required
        />
        <p className="field-hint" id={hintId}>
          Не менее 8 символов.
        </p>
      </div>

      <div className="field">
        <label htmlFor="confirmation">Повторите пароль</label>
        <input
          id="confirmation"
          name="confirmation"
          type="password"
          autoComplete="new-password"
          minLength={8}
          maxLength={128}
          required
        />
      </div>

      <button className="button form-submit" type="submit" disabled={pending}>
        {pending ? "Сохраняем…" : "Сохранить новый пароль"}
      </button>

      <p className="form-switch">
        <Link href="/login">← Вернуться ко входу</Link>
      </p>
    </form>
  );
}
