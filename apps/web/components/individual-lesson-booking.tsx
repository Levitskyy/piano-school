"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState, useSyncExternalStore } from "react";

import { apiErrorMessage } from "@/lib/api-error";
import {
  formatIndividualLessonPrice,
  formatSlotDay,
  formatSlotTime,
  type IndividualLessonOffer,
  type LessonPackage,
  type LessonSlot,
} from "@/lib/individual-lessons-shared";

type IndividualLessonBookingProps = {
  offers: IndividualLessonOffer[];
  slots: LessonSlot[];
  packages: LessonPackage[];
  isAuthenticated: boolean;
};

type SlotGroup = {
  key: string;
  label: string;
  slots: LessonSlot[];
};

export function IndividualLessonBooking({
  offers,
  slots,
  packages,
  isAuthenticated,
}: IndividualLessonBookingProps) {
  const router = useRouter();
  const timeZone = useSyncExternalStore(
    () => () => {},
    () => Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
    () => "UTC",
  );
  const [offerId, setOfferId] = useState(offers[0]?.id ?? "");
  const [slotId, setSlotId] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const groups = useMemo<SlotGroup[]>(() => {
    const byDay = new Map<string, LessonSlot[]>();
    for (const slot of slots) {
      const label = formatSlotDay(slot.starts_at, timeZone);
      const existing = byDay.get(label);
      if (existing) existing.push(slot);
      else byDay.set(label, [slot]);
    }
    return [...byDay.entries()].map(([key, daySlots]) => ({
      key,
      label: key,
      slots: daySlots,
    }));
  }, [slots, timeZone]);

  const availablePackages = packages.filter(
    (item) => item.status === "active" && item.remaining_lessons > 0,
  );

  async function send(path: string, body: object) {
    setError(null);
    if (!slotId) {
      setError("Выберите время занятия.");
      return;
    }
    if (!isAuthenticated) {
      router.push(`/login?next=${encodeURIComponent("/individual-lessons")}`);
      return;
    }

    setPending(true);
    try {
      const response = await fetch(`/api/individual-lessons/${path}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        setError(apiErrorMessage(payload));
        return;
      }
      router.push("/account/individual-lessons");
      router.refresh();
    } catch {
      setError("Сервис временно недоступен. Попробуйте ещё раз.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="lesson-booking">
      <div className="booking-step">
        <div className="booking-step-head">
          <span className="step-number">1</span>
          <div>
            <h2>Выберите формат</h2>
            <p>Занятия идут по 60 минут. Цены пока уточняются.</p>
          </div>
        </div>
        <div className="offer-grid">
          {offers.map((offer) => (
            <button
              className={`offer-card offer-choice${offer.id === offerId ? " is-selected" : ""}`}
              key={offer.id}
              type="button"
              aria-pressed={offer.id === offerId}
              onClick={() => setOfferId(offer.id)}
            >
              <p className="card-meta">
                {offer.kind === "single" ? "Разовый урок" : `Пакет из ${offer.lessons_count} уроков`}
              </p>
              <h3>{offer.title}</h3>
              <p>{offer.description}</p>
              <p className="offer-price">
                {formatIndividualLessonPrice(offer)}
              </p>
              {offer.validity_days ? (
                <p className="offer-meta">
                  Действует {offer.validity_days} дней
                </p>
              ) : null}
            </button>
          ))}
        </div>
      </div>

      <div className="booking-step">
        <div className="booking-step-head">
          <span className="step-number">2</span>
          <div>
            <h2>Выберите время</h2>
            <p>
              Время показано в вашем часовом поясе ({timeZone}). Слоты свободны на
              ближайшие 60 дней.
            </p>
          </div>
        </div>

        {groups.length === 0 ? (
          <p className="body-text">Сейчас нет свободных слотов. Загляните позже.</p>
        ) : (
          <div className="slot-groups">
            {groups.map((group) => (
              <section className="slot-group" key={group.key}>
                <h3>{group.label}</h3>
                <div className="slot-grid">
                  {group.slots.map((slot) => (
                    <button
                      className={`slot-button${slot.id === slotId ? " is-selected" : ""}`}
                      key={slot.id}
                      type="button"
                      aria-pressed={slot.id === slotId}
                      onClick={() => setSlotId(slot.id)}
                    >
                      {formatSlotTime(slot.starts_at, timeZone)}
                    </button>
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}
      </div>

      <div className="booking-actions">
        <button
          className="button"
          type="button"
          disabled={pending || !offerId || !slotId}
          onClick={() =>
            send("purchase", {
              offer_id: offerId,
              slot_id: slotId,
            })
          }
        >
          {isAuthenticated ? "Купить и записаться" : "Войти и записаться"}
        </button>
        <p className="booking-note">
          Тестовый режим: слот подтверждается сразу, реальная оплата не списывается.
          Ссылку на встречу преподаватель добавит в кабинете.
        </p>
      </div>

      {availablePackages.length > 0 ? (
        <div className="booking-step">
          <div className="booking-step-head">
            <span className="step-number">3</span>
            <div>
              <h2>У вас есть занятия в пакете</h2>
              <p>Можно записаться на выбранный слот без новой покупки.</p>
            </div>
          </div>
          <div className="package-choice-list">
            {availablePackages.map((item) => (
              <div className="package-choice" key={item.id}>
                <div>
                  <h3>{item.offer_title}</h3>
                  <p>Осталось {item.remaining_lessons} из {item.total_lessons} занятий</p>
                </div>
                <button
                  className="button button-small"
                  type="button"
                  disabled={pending || !slotId}
                  onClick={() =>
                    send("book", {
                      package_id: item.id,
                      slot_id: slotId,
                    })
                  }
                >
                  Записаться
                </button>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {error ? (
        <p className="form-error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
