"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useId, useRef, useState, type FormEvent } from "react";

import { apiErrorMessage } from "@/lib/api-error";

type VerifyEmailFormProps = {
  token: string;
  sent: boolean;
  failed: boolean;
  verified: boolean;
};

export function VerifyEmailForm({
  token,
  sent,
  failed,
  verified,
}: VerifyEmailFormProps) {
  const router = useRouter();
  const messageId = useId();
  const errorRef = useRef<HTMLParagraphElement>(null);
  const startedRef = useRef(false);
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(verified);
  const [message, setMessage] = useState<string | null>(
    sent
      ? "Мы отправили письмо. Откройте ссылку из него, чтобы подтвердить email."
      : failed
        ? "Не удалось отправить письмо. Нажмите кнопку ниже, чтобы попробовать ещё раз."
        : null,
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || startedRef.current) return;
    startedRef.current = true;
    setPending(true);

    async function confirm() {
      try {
        const response = await fetch("/api/auth/verify-email", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ token }),
        });
        if (!response.ok) {
          const payload = await response.json().catch(() => null);
          setError(apiErrorMessage(payload));
          requestAnimationFrame(() => errorRef.current?.focus());
          return;
        }

        setDone(true);
        setMessage(null);
        // Убираем одноразовый токен из адреса: ссылка больше не понадобится.
        router.replace("/verify-email?verified=1");
        router.refresh();
      } catch {
        setError("Сервис временно недоступен. Попробуйте ещё раз.");
        requestAnimationFrame(() => errorRef.current?.focus());
      } finally {
        setPending(false);
      }
    }

    void confirm();
  }, [token, router]);

  if (done) {
    return (
      <div className="form-notice" role="status">
        <p>Email подтверждён. Спасибо!</p>
        <p>
          <Link href="/individual-lessons">Выбрать занятие</Link> ·{" "}
          <Link href="/account">Вернуться в кабинет</Link>
        </p>
      </div>
    );
  }

  async function resend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setPending(true);

    try {
      const response = await fetch("/api/auth/resend-verification", {
        method: "POST",
        headers: { "content-type": "application/json" },
      });
      if (response.status === 401) {
        router.push(`/login?next=${encodeURIComponent("/verify-email")}`);
        return;
      }
      const payload = await response.json().catch(() => null);
      if (!response.ok) {
        setError(apiErrorMessage(payload));
        requestAnimationFrame(() => errorRef.current?.focus());
        return;
      }

      setMessage(
        payload?.verification_email_sent === false
          ? "Не удалось отправить письмо. Попробуйте ещё раз позже."
          : "Мы отправили новую ссылку. Проверьте почту, включая папку «Спам».",
      );
    } catch {
      setError("Сервис временно недоступен. Попробуйте ещё раз.");
      requestAnimationFrame(() => errorRef.current?.focus());
    } finally {
      setPending(false);
    }
  }

  return (
    <form
      className="form"
      method="post"
      action="/api/auth/resend-verification"
      onSubmit={resend}
      aria-labelledby="main-heading"
    >
      {error ? (
        <p className="form-error" role="alert" tabIndex={-1} ref={errorRef}>
          {error}
        </p>
      ) : null}

      <p className="field-hint" id={messageId} role="status" aria-live="polite">
        {message ??
          "Откройте письмо от Levickaya Piano и нажмите на ссылку подтверждения. Ссылка действует 24 часа."}
      </p>

      {token ? (
        <p className="field-hint">
          Если ссылка не сработала, запросите новую — предыдущая перестанет действовать.
        </p>
      ) : null}

      <button className="button form-submit" type="submit" disabled={pending}>
        {pending && token ? "Проверяем ссылку…" : "Отправить письмо ещё раз"}
      </button>

      <p className="form-switch">
        <Link href="/account">Вернуться в кабинет</Link>
      </p>
    </form>
  );
}
