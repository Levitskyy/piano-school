"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState, useSyncExternalStore } from "react";

import { apiErrorMessage } from "@/lib/api-error";
import {
  formatCalendarDate,
  formatCalendarWeekday,
  formatIndividualLessonPrice,
  formatSlotDateTime,
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
  bookingPackage?: LessonPackage | null;
};

type SlotGroup = {
  label: string;
  slots: LessonSlot[];
};

const DAYS_PER_PAGE = 7;

function capitalizeFirst(value: string): string {
  return value.charAt(0).toLocaleUpperCase("ru-RU") + value.slice(1);
}

export function IndividualLessonBooking({
  offers,
  slots,
  packages,
  isAuthenticated,
  bookingPackage = null,
}: IndividualLessonBookingProps) {
  const router = useRouter();
  const timeZone = useSyncExternalStore(
    () => () => {},
    () => Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
    () => "UTC",
  );
  const [offerId, setOfferId] = useState(offers[0]?.id ?? "");
  const [slotId, setSlotId] = useState<string | null>(null);
  const [pageIndex, setPageIndex] = useState(0);
  const [selectedDayLabel, setSelectedDayLabel] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isPackageMode = Boolean(bookingPackage);

  const groups = useMemo<SlotGroup[]>(() => {
    const byDay = new Map<string, LessonSlot[]>();
    for (const slot of slots) {
      const label = formatSlotDay(slot.starts_at, timeZone);
      const existing = byDay.get(label);
      if (existing) existing.push(slot);
      else byDay.set(label, [slot]);
    }
    return [...byDay.entries()].map(([label, daySlots]) => ({
      label,
      slots: daySlots,
    }));
  }, [slots, timeZone]);

  const pageCount = Math.max(1, Math.ceil(groups.length / DAYS_PER_PAGE));
  const currentPage = Math.min(pageIndex, pageCount - 1);
  const visibleGroups = groups.slice(
    currentPage * DAYS_PER_PAGE,
    (currentPage + 1) * DAYS_PER_PAGE,
  );
  const activeGroup =
    visibleGroups.find((group) => group.label === selectedDayLabel) ??
    visibleGroups[0];

  const selectedOffer = isPackageMode
    ? null
    : offers.find((offer) => offer.id === offerId);
  const selectedSlot = slots.find((slot) => slot.id === slotId);
  const selectedTitle = bookingPackage?.offer_title ?? selectedOffer?.title;

  const availablePackages = packages.filter(
    (item) => item.status === "active" && item.remaining_lessons > 0,
  );

  function movePage(direction: -1 | 1) {
    setPageIndex((index) =>
      Math.min(pageCount - 1, Math.max(0, index + direction)),
    );
    setSelectedDayLabel(null);
    setSlotId(null);
  }

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
      {isPackageMode && bookingPackage ? (
        <div className="booking-step">
          <div className="booking-step-head">
            <span className="step-number">✓</span>
            <div>
              <h2>Запись по пакету</h2>
              <p>
                {`${bookingPackage.offer_title}. Осталось ${bookingPackage.remaining_lessons} из ${bookingPackage.total_lessons} занятий.`}
              </p>
            </div>
          </div>
        </div>
      ) : null}

      {!isPackageMode ? (
        <div className="booking-step">
          <div className="booking-step-head">
            <span className="step-number">1</span>
            <div>
              <h2>Выберите формат</h2>
              <p>Занятия идут по 60 минут. Цены пока уточняются.</p>
            </div>
          </div>
          <div className="offer-grid" role="radiogroup" aria-label="Формат занятий">
            {offers.map((offer) => (
              <label className="offer-card offer-choice" key={offer.id}>
                <input
                  className="offer-choice-input"
                  type="radio"
                  name="lesson-offer"
                  value={offer.id}
                  checked={offer.id === offerId}
                  onChange={() => setOfferId(offer.id)}
                />
                <p className="card-meta">
                  {offer.kind === "single"
                    ? "Разовый урок"
                    : `Пакет из ${offer.lessons_count} уроков`}
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
              </label>
            ))}
          </div>
        </div>
      ) : null}

      <div className="booking-step">
        <div className="booking-step-head">
          <span className="step-number">{isPackageMode ? "1" : "2"}</span>
          <div>
            <h2>Выберите дату и время</h2>
            <p>
              Время показано в вашем часовом поясе ({timeZone}). Слоты свободны на
              ближайшие 60 дней.
            </p>
          </div>
        </div>

        {groups.length === 0 ? (
          <p className="body-text">Сейчас нет свободных слотов. Загляните позже.</p>
        ) : (
          <div className="calendar">
            <div className="calendar-bar">
              <div>
                <h3>Свободные даты</h3>
                <p>
                  Неделя {currentPage + 1} из {pageCount} · всего {groups.length} дней
                </p>
              </div>
              <div className="calendar-nav">
                <button
                  className="calendar-nav-button"
                  type="button"
                  aria-label="Предыдущие даты"
                  disabled={currentPage === 0}
                  onClick={() => movePage(-1)}
                >
                  ←
                </button>
                <button
                  className="calendar-nav-button"
                  type="button"
                  aria-label="Следующие даты"
                  disabled={currentPage === pageCount - 1}
                  onClick={() => movePage(1)}
                >
                  →
                </button>
              </div>
            </div>

            <div className="calendar-days" role="group" aria-label="Даты занятий">
              {visibleGroups.map((group) => (
                <button
                  className="calendar-day"
                  key={group.label}
                  type="button"
                  aria-pressed={group.label === activeGroup?.label}
                  aria-label={`${group.label}, свободных слотов: ${group.slots.length}`}
                  onClick={() => {
                    setSelectedDayLabel(group.label);
                    setSlotId(null);
                  }}
                >
                  <span className="calendar-weekday">
                    {formatCalendarWeekday(group.slots[0].starts_at, timeZone)}
                  </span>
                  <span className="calendar-date">
                    {formatCalendarDate(group.slots[0].starts_at, timeZone)}
                  </span>
                  <span className="calendar-count">
                    {group.slots.length} свободно
                  </span>
                </button>
              ))}
            </div>

            {activeGroup ? (
              <div className="calendar-panel">
                <div className="calendar-panel-head">
                  <h4>{capitalizeFirst(activeGroup.label)}</h4>
                  <p>{activeGroup.slots.length} доступных слотов</p>
                </div>
                <div className="calendar-times" role="group" aria-label="Время занятий">
                  {activeGroup.slots.map((slot) => (
                    <button
                      className="time-button"
                      key={slot.id}
                      type="button"
                      aria-pressed={slot.id === slotId}
                      onClick={() => setSlotId(slot.id)}
                    >
                      <span>{formatSlotTime(slot.starts_at, timeZone)}</span>
                      <small>{slot.duration_minutes} мин</small>
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        )}

        <p className="selection-summary" role="status">
          {selectedTitle && selectedSlot
            ? `Выбрано: ${selectedTitle}, ${formatSlotDateTime(selectedSlot.starts_at, timeZone)}`
            : isPackageMode
              ? "Выберите время, чтобы записаться на урок."
              : "Выберите формат и время, чтобы продолжить."}
        </p>
      </div>

      <div className="booking-actions">
        <button
          className="button"
          type="button"
          disabled={pending || !slotId || (!isPackageMode && !offerId)}
          onClick={() =>
            isPackageMode && bookingPackage
              ? send("book", {
                  package_id: bookingPackage.id,
                  slot_id: slotId,
                })
              : send("purchase", {
                  offer_id: offerId,
                  slot_id: slotId,
                })
          }
        >
          {isPackageMode
            ? "Записаться на урок"
            : isAuthenticated
              ? "Купить и записаться"
              : "Войти и записаться"}
        </button>
        {!isPackageMode ? (
          <p className="booking-note">
            Тестовый режим: слот подтверждается сразу, реальная оплата не
            списывается. Ссылку на встречу преподаватель добавит в кабинете.
          </p>
        ) : null}
      </div>

      {!isPackageMode && availablePackages.length > 0 ? (
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
                  <p>
                    Осталось {item.remaining_lessons} из {item.total_lessons} занятий
                  </p>
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
