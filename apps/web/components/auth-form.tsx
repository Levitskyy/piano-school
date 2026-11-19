"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useId, useRef, useState } from "react";

import { apiErrorMessage } from "@/lib/api-error";

type Mode = "login" | "register";

type AuthFormProps = {
  mode: Mode;
  headingId: string;
  next?: string;
};

export function AuthForm({ mode, headingId, next }: AuthFormProps) {
  const router = useRouter();
  const errorId = useId();
  const passwordHintId = useId();
  const errorRef = useRef<HTMLParagraphElement>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const isLogin = mode === "login";

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setPending(true);

    const form = event.currentTarget;
    const data = new FormData(form);
    const payload = isLogin
      ? {
          email: String(data.get("email") ?? ""),
          password: String(data.get("password") ?? ""),
        }
      : {
          name: String(data.get("name") ?? ""),
          email: String(data.get("email") ?? ""),
          password: String(data.get("password") ?? ""),
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        };

    try {
      const response = await fetch(`/api/auth/${isLogin ? "login" : "register"}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await response.json().catch(() => null);

      if (!response.ok) {
        setError(apiErrorMessage(body));
        requestAnimationFrame(() => errorRef.current?.focus());
        return;
      }

      const safeNext = next?.startsWith("/") && !next.startsWith("//") ? next : "/account";
      router.push(safeNext);
      router.refresh();
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
      action={`/api/auth/${isLogin ? "login" : "register"}`}
      onSubmit={handleSubmit}
      aria-labelledby={headingId}
    >
      {error ? (
        <p
          className="form-error"
          id={errorId}
          role="alert"
          tabIndex={-1}
          ref={errorRef}
        >
          {error}
        </p>
      ) : null}

      {!isLogin ? (
        <div className="field">
          <label htmlFor="name">Имя</label>
          <input
            id="name"
            name="name"
            type="text"
            autoComplete="name"
            enterKeyHint="next"
            maxLength={120}
            required
          />
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
          enterKeyHint="next"
          required
        />
      </div>

      <div className="field">
        <label htmlFor="password">Пароль</label>
        <div className="password-row">
          <input
            id="password"
            name="password"
            type={showPassword ? "text" : "password"}
            autoComplete={isLogin ? "current-password" : "new-password"}
            minLength={8}
            maxLength={128}
            enterKeyHint="done"
            aria-describedby={passwordHintId}
            required
          />
          <button
            className="password-toggle"
            type="button"
            aria-pressed={showPassword}
            aria-label={showPassword ? "Скрыть пароль" : "Показать пароль"}
            onClick={() => setShowPassword((value) => !value)}
          >
            {showPassword ? "Скрыть" : "Показать"}
          </button>
        </div>
        <p className="field-hint" id={passwordHintId}>
          {isLogin ? "Пароль от вашего аккаунта." : "Не менее 8 символов."}
        </p>
      </div>

      <button className="button form-submit" type="submit" disabled={pending}>
        {pending
          ? isLogin
            ? "Входим…"
            : "Создаём аккаунт…"
          : isLogin
            ? "Войти"
            : "Создать аккаунт"}
      </button>

      <p className="form-switch">
        {isLogin ? (
          <>
            Нет аккаунта? <Link href="/register">Зарегистрироваться</Link>
          </>
        ) : (
          <>
            Уже есть аккаунт? <Link href="/login">Войти</Link>
          </>
        )}
      </p>

      {isLogin ? (
        <p className="form-switch">
          <Link href="/forgot-password">Забыли пароль?</Link>
        </p>
      ) : null}
    </form>
  );
}
