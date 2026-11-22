"use client";

import { useId, useState, type FormEvent } from "react";

import { apiErrorMessage } from "@/lib/api-error";

type PromoCode = {
  id: string;
  code: string;
  discount_percent: string | number;
  is_active: boolean;
  used_at: string | null;
  created_at: string;
};

type AdminPromoFormProps = {
  promoCodes: PromoCode[];
};

function promoStatus(promo: PromoCode): string {
  if (promo.used_at) return "использован";
  return promo.is_active ? "активен" : "неактивен";
}

function formatPercent(value: string | number): string {
  return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 2 }).format(
    Number(value),
  );
}

export function AdminPromoForm({ promoCodes: initialCodes }: AdminPromoFormProps) {
  const [codes, setCodes] = useState(initialCodes);
  const [percent, setPercent] = useState("33.33");
  const [code, setCode] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const percentId = useId();
  const codeId = useId();

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setPending(true);

    try {
      const response = await fetch("/api/admin/promo-codes", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          percent,
          code: code.trim() || null,
        }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        setError(apiErrorMessage(payload));
        return;
      }

      const created = (await response.json()) as PromoCode;
      setCodes((current) => [created, ...current]);
      setMessage(
        `Промокод ${created.code} создан: скидка ${formatPercent(
          created.discount_percent,
        )}%. Код одноразовый.`,
      );
      setPercent("33.33");
      setCode("");
    } catch {
      setError("Не удалось создать промокод. Попробуйте ещё раз.");
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <section className="panel-section" aria-labelledby="promo-create-title">
        <div className="panel-section-head">
          <h2 id="promo-create-title">Новый промокод</h2>
          <p className="muted">
            Скидка в процентах, один код на одну покупку. Без названия код сгенерируется
            автоматически.
          </p>
        </div>

        <form className="form form-wide" onSubmit={submit}>
          <div className="field">
            <label htmlFor={percentId}>Скидка, %</label>
            <input
              id={percentId}
              name="percent"
              type="number"
              min="0.01"
              max="100"
              step="0.01"
              required
              value={percent}
              onChange={(event) => setPercent(event.target.value)}
            />
            <p className="field-hint">Например, 33,33 — с 1 500 ₽ получится 1 000 ₽.</p>
          </div>

          <div className="field">
            <label htmlFor={codeId}>Код (необязательно)</label>
            <input
              id={codeId}
              name="code"
              type="text"
              maxLength={32}
              autoComplete="off"
              placeholder="Например, PERVIY"
              value={code}
              onChange={(event) => setCode(event.target.value)}
            />
          </div>

          <button className="button form-submit" type="submit" disabled={pending}>
            {pending ? "Создаём…" : "Создать промокод"}
          </button>

          {error ? <p className="form-error" role="alert">{error}</p> : null}
          {message ? (
            <p className="form-notice" aria-live="polite">{message}</p>
          ) : null}
        </form>
      </section>

      <section className="panel-section" aria-labelledby="promo-list-title">
        <div className="panel-section-head">
          <h2 id="promo-list-title">Созданные коды</h2>
        </div>

        {codes.length ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th scope="col">Код</th>
                  <th scope="col">Скидка</th>
                  <th scope="col">Статус</th>
                  <th scope="col">Создан</th>
                </tr>
              </thead>
              <tbody>
                {codes.map((promo) => (
                  <tr key={promo.id}>
                    <th scope="row">{promo.code}</th>
                    <td>{formatPercent(promo.discount_percent)}%</td>
                    <td>{promoStatus(promo)}</td>
                    <td>{promo.created_at.slice(0, 10)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="muted">Промокодов пока нет.</p>
        )}
      </section>
    </>
  );
}
