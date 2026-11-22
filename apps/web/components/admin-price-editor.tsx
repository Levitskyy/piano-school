"use client";

import { useState, type FormEvent } from "react";

import { apiErrorMessage } from "@/lib/api-error";
import {
  formatIndividualLessonPrice,
  type IndividualLessonOffer,
} from "@/lib/individual-lessons-shared";

type AdminPriceEditorProps = {
  offers: IndividualLessonOffer[];
};

function priceInputValue(offer: IndividualLessonOffer): string {
  return offer.price_minor === null ? "" : String(offer.price_minor / 100);
}

export function AdminPriceEditor({ offers: initialOffers }: AdminPriceEditorProps) {
  const [offers, setOffers] = useState(initialOffers);
  const [drafts, setDrafts] = useState<Record<string, string>>(() =>
    Object.fromEntries(initialOffers.map((offer) => [offer.slug, priceInputValue(offer)])),
  );
  const [pendingSlug, setPendingSlug] = useState<string | null>(null);
  const [savedSlug, setSavedSlug] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function save(slug: string, event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setSavedSlug(null);
    setPendingSlug(slug);

    try {
      const response = await fetch(
        `/api/admin/products/${encodeURIComponent(slug)}/price`,
        {
          method: "PATCH",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ price: drafts[slug] }),
        },
      );

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        setError(apiErrorMessage(payload));
        return;
      }

      const updated = (await response.json()) as IndividualLessonOffer;
      setOffers((current) =>
        current.map((offer) => (offer.slug === updated.slug ? updated : offer)),
      );
      setDrafts((current) => ({ ...current, [slug]: priceInputValue(updated) }));
      setSavedSlug(slug);
      setMessage(`Сохранено: ${updated.title} — ${formatIndividualLessonPrice(updated)}`);
    } catch {
      setError("Не удалось сохранить цену. Попробуйте ещё раз.");
    } finally {
      setPendingSlug(null);
    }
  }

  return (
    <section className="panel-section" aria-labelledby="prices-title">
      <div className="panel-section-head">
        <h2 id="prices-title">Тарифы</h2>
        <p className="muted">
          Цена в рублях. После сохранения новую сумму увидит страница записи и ЮKassa.
        </p>
      </div>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Тариф</th>
              <th scope="col">Сейчас</th>
              <th scope="col">Новая цена, ₽</th>
              <th scope="col">
                <span className="visually-hidden">Действие</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {offers.map((offer) => {
              const inputId = `admin-price-${offer.slug}`;
              const isPending = pendingSlug === offer.slug;
              return (
                <tr key={offer.slug}>
                  <th scope="row">
                    {offer.title}
                    <br />
                    <span className="muted">{offer.slug}</span>
                  </th>
                  <td>{formatIndividualLessonPrice(offer)}</td>
                  <td>
                    <form className="price-form" onSubmit={(event) => save(offer.slug, event)}>
                      <label className="visually-hidden" htmlFor={inputId}>
                        Цена для {offer.title} в рублях
                      </label>
                      <input
                        id={inputId}
                        name="price"
                        type="number"
                        min="1"
                        step="0.01"
                        required
                        value={drafts[offer.slug] ?? ""}
                        onChange={(event) =>
                          setDrafts((current) => ({
                            ...current,
                            [offer.slug]: event.target.value,
                          }))
                        }
                      />
                      <button
                        className="button button-small"
                        type="submit"
                        disabled={isPending || pendingSlug !== null}
                      >
                        {isPending ? "Сохраняем…" : "Сохранить"}
                      </button>
                    </form>
                  </td>
                  <td>
                    {isPending ? (
                      <span className="muted">…</span>
                    ) : savedSlug === offer.slug ? (
                      <span className="muted">✓</span>
                    ) : null}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {error ? (
        <p className="form-error" role="alert">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="form-notice" aria-live="polite">
          {message}
        </p>
      ) : null}
    </section>
  );
}
