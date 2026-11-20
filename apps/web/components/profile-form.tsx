"use client";

import { useRouter } from "next/navigation";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import { apiErrorMessage } from "@/lib/api-error";
import {
  detectBrowserTimezone,
  formatTimeInTimezone,
  getTimezoneGroup,
  getTimezoneLabel,
  getTimezoneOffset,
  getTimezoneOptions,
  groupTimezoneOptions,
  timezoneGroupOrder,
} from "@/lib/timezones";

type ProfileFormProps = {
  initialName: string;
  initialTimezone: string;
  email: string;
};

export function ProfileForm({ initialName, initialTimezone, email }: ProfileFormProps) {
  const router = useRouter();
  const errorRef = useRef<HTMLParagraphElement>(null);
  const hintId = useId();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [timezone, setTimezone] = useState(initialTimezone);
  const [query, setQuery] = useState("");
  const [now, setNow] = useState<Date | null>(null);

  const options = useMemo(() => getTimezoneOptions(), []);
  const visibleOptions = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase("ru");
    if (!needle) return options;
    return options.filter(
      (option) =>
        option.label.toLocaleLowerCase("ru").includes(needle) ||
        option.value.toLocaleLowerCase("ru").includes(needle),
    );
  }, [options, query]);
  const groupedOptions = useMemo(
    () => groupTimezoneOptions(visibleOptions),
    [visibleOptions],
  );
  const currentOptionVisible = visibleOptions.some((option) => option.value === timezone);

  useEffect(() => {
    const update = () => setNow(new Date());
    const initial = window.setTimeout(update, 0);
    const timer = window.setInterval(update, 30_000);
    return () => {
      window.clearTimeout(initial);
      window.clearInterval(timer);
    };
  }, []);

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
          timezone,
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

  function handleDetect() {
    const detected = detectBrowserTimezone();
    if (!detected) {
      setError("Не удалось определить часовой пояс. Выберите город в списке.");
      requestAnimationFrame(() => errorRef.current?.focus());
      return;
    }
    setError(null);
    setMessage(null);
    setQuery("");
    setTimezone(detected);
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
        <label htmlFor="timezone-search">Поиск часового пояса</label>
        <input
          id="timezone-search"
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Например, Москва или Токио"
          autoComplete="off"
          aria-describedby={hintId}
        />
      </div>

      <div className="field">
        <label htmlFor="timezone">Часовой пояс</label>
        <select
          id="timezone"
          name="timezone"
          value={timezone}
          onChange={(event) => setTimezone(event.target.value)}
          aria-describedby={hintId}
          required
        >
          {currentOptionVisible ? null : (
            <option value={timezone}>
              {getTimezoneLabel(timezone)} — текущий
            </option>
          )}
          {groupedOptions.map((group, index) =>
            group.length === 0 ? null : (
              <optgroup key={timezoneGroupOrder[index]} label={timezoneGroupOrder[index]}>
                {group.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </optgroup>
            ),
          )}
        </select>

        <div className="timezone-controls">
          <button
            className="button button-ghost button-small"
            type="button"
            onClick={handleDetect}
          >
            Определить автоматически
          </button>
          <span className="timezone-region">
            {getTimezoneGroup(timezone)}
          </span>
        </div>

        <p className="field-hint" id={hintId}>
          {now
            ? `Сейчас в выбранном поясе: ${formatTimeInTimezone(timezone, now)} (${getTimezoneOffset(timezone, now)}).`
            : "Выберите город из списка — время для расписания занятий будет показано локально."}
        </p>
      </div>

      <button className="button form-submit" type="submit" disabled={pending}>
        {pending ? "Сохраняем…" : "Сохранить"}
      </button>
    </form>
  );
}
