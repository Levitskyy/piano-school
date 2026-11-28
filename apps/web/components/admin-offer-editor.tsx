"use client";

import { useId, useState, type FormEvent } from "react";

import { apiErrorMessage } from "@/lib/api-error";
import {
  formatIndividualLessonPrice,
  type IndividualLessonOffer,
} from "@/lib/individual-lessons-shared";

type AdminOffer = IndividualLessonOffer & {
  is_active: boolean;
  position: number;
};

type OfferDraft = {
  title: string;
  description: string;
  lessonsCount: string;
  price: string;
  validityDays: string;
};

type AdminOfferEditorProps = {
  offers: AdminOffer[];
};

const emptyDraft: OfferDraft = {
  title: "",
  description: "",
  lessonsCount: "4",
  price: "",
  validityDays: "",
};

function draftFromOffer(offer: AdminOffer): OfferDraft {
  return {
    title: offer.title,
    description: offer.description,
    lessonsCount: String(offer.lessons_count),
    price: offer.price_minor === null ? "" : String(offer.price_minor / 100),
    validityDays: offer.validity_days === null ? "" : String(offer.validity_days),
  };
}

function draftPayload(draft: OfferDraft) {
  return {
    title: draft.title,
    description: draft.description,
    lessons_count: Number(draft.lessonsCount),
    price: draft.price,
    validity_days:
      draft.validityDays.trim() === "" ? null : Number(draft.validityDays),
  };
}

export function AdminOfferEditor({ offers: initialOffers }: AdminOfferEditorProps) {
  const formId = useId();
  const [offers, setOffers] = useState(initialOffers);
  const [drafts, setDrafts] = useState<Record<string, OfferDraft>>(() =>
    Object.fromEntries(initialOffers.map((offer) => [offer.slug, draftFromOffer(offer)])),
  );
  const [newDraft, setNewDraft] = useState<OfferDraft>(emptyDraft);
  const [newSlug, setNewSlug] = useState("");
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  function setDraftField(
    draftsMap: Record<string, OfferDraft>,
    slug: string,
    field: keyof OfferDraft,
    value: string,
  ): Record<string, OfferDraft> {
    return {
      ...draftsMap,
      [slug]: { ...draftsMap[slug], [field]: value },
    };
  }

  function replaceOffer(updated: AdminOffer) {
    setOffers((current) =>
      current.map((offer) => (offer.slug === updated.slug ? updated : offer)),
    );
  }

  async function saveOffer(offer: AdminOffer, event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setPending(offer.slug);

    try {
      const response = await fetch(
        `/api/admin/products/${encodeURIComponent(offer.slug)}`,
        {
          method: "PATCH",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(draftPayload(drafts[offer.slug] ?? draftFromOffer(offer))),
        },
      );
      if (!response.ok) {
        setError(apiErrorMessage(await response.json().catch(() => null)));
        return;
      }
      const updated = (await response.json()) as AdminOffer;
      replaceOffer(updated);
      setDrafts((current) =>
        setDraftField(current, offer.slug, "price", draftFromOffer(updated).price),
      );
      setMessage(`Сохранено: ${updated.title}`);
    } catch {
      setError("Не удалось сохранить тариф. Попробуйте ещё раз.");
    } finally {
      setPending(null);
    }
  }

  async function toggleActive(offer: AdminOffer) {
    setError(null);
    setMessage(null);
    setPending(offer.slug);

    try {
      const response = await fetch(`/api/admin/products/${encodeURIComponent(offer.slug)}`, {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ is_active: !offer.is_active }),
      });
      if (!response.ok) {
        setError(apiErrorMessage(await response.json().catch(() => null)));
        return;
      }
      const updated = (await response.json()) as AdminOffer;
      replaceOffer(updated);
      setMessage(updated.is_active ? "Тариф показан на сайте" : "Тариф скрыт с сайта");
    } catch {
      setError("Не удалось изменить видимость тарифа.");
    } finally {
      setPending(null);
    }
  }

  async function deleteOffer(offer: AdminOffer) {
    if (
      !window.confirm(
        `Удалить тариф «${offer.title}»? Если он уже использовался в заказах или пакетах, удаление будет отказано — такой тариф лучше скрыть.`,
      )
    ) {
      return;
    }
    setError(null);
    setMessage(null);
    setPending(offer.slug);

    try {
      const response = await fetch(`/api/admin/products/${encodeURIComponent(offer.slug)}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        setError(apiErrorMessage(await response.json().catch(() => null)));
        return;
      }
      setOffers((current) => current.filter((item) => item.slug !== offer.slug));
      setDrafts((current) => {
        const next = { ...current };
        delete next[offer.slug];
        return next;
      });
      setMessage(`Удалён тариф «${offer.title}»`);
    } catch {
      setError("Не удалось удалить тариф. Попробуйте ещё раз.");
    } finally {
      setPending(null);
    }
  }

  async function createOffer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setPending("new");

    try {
      const response = await fetch("/api/admin/products", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          ...draftPayload(newDraft),
          slug: newSlug.trim() || undefined,
        }),
      });
      if (!response.ok) {
        setError(apiErrorMessage(await response.json().catch(() => null)));
        return;
      }
      const created = (await response.json()) as AdminOffer;
      setOffers((current) => [...current, created]);
      setDrafts((current) => ({
        ...current,
        [created.slug]: draftFromOffer(created),
      }));
      setNewDraft(emptyDraft);
      setNewSlug("");
      setMessage(`Добавлен тариф «${created.title}» (ключ: ${created.slug})`);
    } catch {
      setError("Не удалось добавить тариф. Попробуйте ещё раз.");
    } finally {
      setPending(null);
    }
  }

  return (
    <>
      <section className="panel-section" aria-labelledby="offers-title">
        <div className="panel-section-head">
          <h2 id="offers-title">Тарифы и пакеты</h2>
          <p className="muted">
            Название, описание, число уроков, цена и срок действия сразу видны на странице
            записи. Скрытый тариф остаётся в базе, но недоступен для покупки.
          </p>
        </div>

        <div className="offer-admin-list">
          {offers.map((offer) => {
            const draft = drafts[offer.slug] ?? draftFromOffer(offer);
            const isPending = pending === offer.slug;
            return (
              <form
                className={`offer-admin-card${offer.is_active ? "" : " is-inactive"}`}
                key={offer.slug}
                onSubmit={(event) => saveOffer(offer, event)}
              >
                <div className="offer-admin-grid">
                  <div className="field">
                    <label htmlFor={`offer-title-${offer.slug}`}>Название</label>
                    <input
                      id={`offer-title-${offer.slug}`}
                      value={draft.title}
                      maxLength={200}
                      required
                      onChange={(event) =>
                        setDrafts((current) =>
                          setDraftField(current, offer.slug, "title", event.target.value),
                        )
                      }
                    />
                  </div>
                  <div className="field">
                    <label htmlFor={`offer-count-${offer.slug}`}>Уроков в пакете</label>
                    <input
                      id={`offer-count-${offer.slug}`}
                      type="number"
                      min={1}
                      max={100}
                      required
                      value={draft.lessonsCount}
                      onChange={(event) =>
                        setDrafts((current) =>
                          setDraftField(current, offer.slug, "lessonsCount", event.target.value),
                        )
                      }
                    />
                  </div>
                  <div className="field">
                    <label htmlFor={`offer-price-${offer.slug}`}>Цена, ₽</label>
                    <input
                      id={`offer-price-${offer.slug}`}
                      type="number"
                      min={1}
                      step={0.01}
                      required
                      value={draft.price}
                      onChange={(event) =>
                        setDrafts((current) =>
                          setDraftField(current, offer.slug, "price", event.target.value),
                        )
                      }
                    />
                  </div>
                  <div className="field">
                    <label htmlFor={`offer-validity-${offer.slug}`}>Действует, дней</label>
                    <input
                      id={`offer-validity-${offer.slug}`}
                      type="number"
                      min={1}
                      max={3650}
                      value={draft.validityDays}
                      onChange={(event) =>
                        setDrafts((current) =>
                          setDraftField(current, offer.slug, "validityDays", event.target.value),
                        )
                      }
                    />
                    <p className="field-hint">Пусто — без срока</p>
                  </div>
                  <div className="field field-wide">
                    <label htmlFor={`offer-description-${offer.slug}`}>Описание</label>
                    <textarea
                      id={`offer-description-${offer.slug}`}
                      rows={2}
                      maxLength={2000}
                      value={draft.description}
                      onChange={(event) =>
                        setDrafts((current) =>
                          setDraftField(current, offer.slug, "description", event.target.value),
                        )
                      }
                    />
                  </div>
                </div>
                <div className="offer-admin-actions">
                  <p className="muted">
                    <code>{offer.slug}</code> · {formatIndividualLessonPrice(offer)} ·{" "}
                    {offer.is_active ? "виден на сайте" : "скрыт"}
                  </p>
                  <div className="offer-admin-actions-group">
                    <button className="button button-small" type="submit" disabled={isPending}>
                      {isPending ? "Сохраняем…" : "Сохранить"}
                    </button>
                    <button
                      className="button button-small button-ghost"
                      type="button"
                      disabled={isPending}
                      onClick={() => toggleActive(offer)}
                    >
                      {offer.is_active ? "Скрыть" : "Показать"}
                    </button>
                    <button
                      className="button button-small button-ghost"
                      type="button"
                      disabled={isPending}
                      onClick={() => deleteOffer(offer)}
                    >
                      Удалить
                    </button>
                  </div>
                </div>
              </form>
            );
          })}
        </div>
      </section>

      <section className="panel-section" aria-labelledby={`${formId}-title`}>
        <div className="panel-section-head">
          <h2 id={`${formId}-title`}>Новый тариф</h2>
          <p className="muted">
            Ключ заполнять не обязательно: без него он будет создан из названия. Ключ нужен только
            для CLI-команд и промокодов.
          </p>
        </div>
        <form className="form form-wide" onSubmit={createOffer}>
          <div className="field">
            <label htmlFor={`${formId}-title-input`}>Название</label>
            <input
              id={`${formId}-title-input`}
              value={newDraft.title}
              maxLength={200}
              required
              onChange={(event) =>
                setNewDraft((current) => ({ ...current, title: event.target.value }))
              }
            />
          </div>
          <div className="field">
            <label htmlFor={`${formId}-slug`}>Ключ (необязательно)</label>
            <input
              id={`${formId}-slug`}
              value={newSlug}
              maxLength={80}
              placeholder="package-6"
              onChange={(event) => setNewSlug(event.target.value)}
            />
            <p className="field-hint">Латинские буквы, цифры и дефис.</p>
          </div>
          <div className="field">
            <label htmlFor={`${formId}-description`}>Описание</label>
            <textarea
              id={`${formId}-description`}
              rows={3}
              maxLength={2000}
              value={newDraft.description}
              onChange={(event) =>
                setNewDraft((current) => ({ ...current, description: event.target.value }))
              }
            />
          </div>
          <div className="field">
            <label htmlFor={`${formId}-count`}>Уроков в пакете</label>
            <input
              id={`${formId}-count`}
              type="number"
              min={1}
              max={100}
              required
              value={newDraft.lessonsCount}
              onChange={(event) =>
                setNewDraft((current) => ({ ...current, lessonsCount: event.target.value }))
              }
            />
          </div>
          <div className="field">
            <label htmlFor={`${formId}-price`}>Цена, ₽</label>
            <input
              id={`${formId}-price`}
              type="number"
              min={1}
              step={0.01}
              required
              value={newDraft.price}
              onChange={(event) =>
                setNewDraft((current) => ({ ...current, price: event.target.value }))
              }
            />
          </div>
          <div className="field">
            <label htmlFor={`${formId}-validity`}>Действует, дней</label>
            <input
              id={`${formId}-validity`}
              type="number"
              min={1}
              max={3650}
              value={newDraft.validityDays}
              onChange={(event) =>
                setNewDraft((current) => ({ ...current, validityDays: event.target.value }))
              }
            />
            <p className="field-hint">Пусто — без срока; на сайте появится «Действует N дней».</p>
          </div>
          <button className="button form-submit" type="submit" disabled={pending !== null}>
            {pending === "new" ? "Добавляем…" : "Добавить тариф"}
          </button>
        </form>
      </section>

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
    </>
  );
}
