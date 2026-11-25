"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState, useSyncExternalStore, type FormEvent } from "react";

import { apiErrorMessage } from "@/lib/api-error";
import {
  formatCalendarDate,
  formatCalendarWeekday,
  formatIndividualLessonPrice,
  formatSlotDateTime,
  formatSlotDay,
  formatSlotTime,
  type IndividualLessonOffer,
  type LessonBooking,
  type LessonPackage,
  type LessonSlot,
} from "@/lib/individual-lessons-shared";

type IndividualLessonBookingProps = {
  offers: IndividualLessonOffer[];
  slots: LessonSlot[];
  packages: LessonPackage[];
  isAuthenticated: boolean;
  emailVerificationRequired?: boolean;
  bookingPackage?: LessonPackage | null;
  rescheduleBooking?: Pick<LessonBooking, "id" | "offer_title" | "starts_at"> | null;
  timeZoneOverride?: string | null;
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
  emailVerificationRequired = false,
  bookingPackage = null,
  rescheduleBooking = null,
  timeZoneOverride = null,
}: IndividualLessonBookingProps) {
  const router = useRouter();
  const browserTimeZone = useSyncExternalStore(
    () => () => {},
    () => Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
    () => "UTC",
  );
  const timeZone = timeZoneOverride || browserTimeZone;
  const [offerId, setOfferId] = useState(offers[0]?.id ?? "");
  const [slotId, setSlotId] = useState<string | null>(null);
  const [pageIndex, setPageIndex] = useState(0);
  const [selectedDayLabel, setSelectedDayLabel] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [promoCode, setPromoCode] = useState("");
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isPackageMode = Boolean(bookingPackage);
  const isRescheduleMode = Boolean(rescheduleBooking);

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
  const selectedTitle =
    rescheduleBooking?.offer_title ??
    bookingPackage?.offer_title ??
    selectedOffer?.title;

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
    if (emailVerificationRequired) {
      setError("Подтвердите email, чтобы записаться на урок.");
      return;
    }
    if (!slotId) {
      setError("Выберите время занятия.");
      return;
    }
    if (!isAuthenticated) {
      const nextPath = rescheduleBooking
        ? `/account/individual-lessons/bookings/${rescheduleBooking.id}/reschedule`
        : "/individual-lessons";
      router.push(`/login?next=${encodeURIComponent(nextPath)}`);
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

  async function purchase() {
    setError(null);
    if (emailVerificationRequired) {
      setError("Подтвердите email, чтобы оплатить занятие.");
      return;
    }
    if (!slotId) {
      setError("Выберите время занятия.");
      return;
    }
    if (!offerId) {
      setError("Выберите формат занятия.");
      return;
    }
    if (!consent) {
      setError("Примите условия оферты и политики конфиденциальности.");
      return;
    }
    if (!isAuthenticated) {
      router.push(`/login?next=${encodeURIComponent("/individual-lessons")}`);
      return;
    }

    setPending(true);
    try {
      const response = await fetch("/api/individual-lessons/purchase", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          offer_id: offerId,
          slot_id: slotId,
          promo_code: promoCode.trim() || null,
        }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        setError(apiErrorMessage(payload));
        return;
      }
      const data = await response.json();
      if (typeof data.confirmation_url !== "string") {
        setError("Не удалось получить ссылку на оплату. Попробуйте ещё раз.");
        return;
      }
      window.location.assign(data.confirmation_url);
    } catch {
      setError("Сервис временно недоступен. Попробуйте ещё раз.");
    } finally {
      setPending(false);
    }
  }

  function onSubmitPurchase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void purchase();
  }

  return (
    <div className="lesson-booking">
      {emailVerificationRequired ? (
        <div className="form-notice verification-notice" role="status">
          <p>
            Подтвердите email, чтобы оплатить занятие и записаться на урок. Кабинет и
            расписание доступны сразу.
          </p>
          <p>
            <Link href="/verify-email">Открыть инструкцию</Link>
          </p>
        </div>
      ) : null}

      {isRescheduleMode && rescheduleBooking ? (
        <div className="booking-step">
          <div className="booking-step-head">
            <span className="step-number">↺</span>
            <div>
              <h2>Перенос занятия</h2>
              <p>
                {`${rescheduleBooking.offer_title}. Сейчас занятие назначено на ${formatSlotDateTime(rescheduleBooking.starts_at, timeZone)}.`}
              </p>
            </div>
          </div>
        </div>
      ) : null}

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

      {!isPackageMode && !isRescheduleMode ? (
        <div className="booking-step">
          <div className="booking-step-head">
            <span className="step-number">1</span>
            <div>
              <h2>Выберите формат</h2>
              <p>Занятия идут по 60 минут. Цена указана в каждом формате.</p>
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
          <span className="step-number">
            {isPackageMode || isRescheduleMode ? "1" : "2"}
          </span>
          <div>
            <h2>Выберите дату и время</h2>
            <p>
              Время показано в вашем часовом поясе ({timeZone}). Слоты свободны на
              ближайшие 60 дней.
              {isAuthenticated
                ? " Дни, на которые вы уже записаны, скрыты."
                : ""}
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
            : isRescheduleMode
              ? "Выберите новое время, чтобы перенести занятие."
              : isPackageMode
                ? "Выберите время, чтобы записаться на урок."
                : "Выберите формат и время, чтобы продолжить."}
        </p>
      </div>

      {isRescheduleMode && rescheduleBooking ? (
        <div className="booking-actions">
          <button
            className="button"
            type="button"
            disabled={pending || !slotId || emailVerificationRequired}
            onClick={() =>
              send(`bookings/${rescheduleBooking.id}/reschedule`, {
                slot_id: slotId,
              })
            }
          >
            Перенести занятие
          </button>
          <p className="booking-note">
            Старое время освободится, а занятие останется в том же пакете.
          </p>
        </div>
      ) : isPackageMode ? (
        <div className="booking-actions">
          <button
            className="button"
            type="button"
            disabled={
              pending || !slotId || !bookingPackage || emailVerificationRequired
            }
            onClick={() =>
              bookingPackage &&
              send("book", { package_id: bookingPackage.id, slot_id: slotId })
            }
          >
            Записаться на урок
          </button>
        </div>
      ) : (
        <form className="booking-actions" onSubmit={onSubmitPurchase}>
          <div className="field">
            <label htmlFor="promo-code">Промокод</label>
            <input
              id="promo-code"
              name="promo_code"
              type="text"
              value={promoCode}
              onChange={(event) => setPromoCode(event.target.value)}
              aria-describedby="promo-hint"
              autoComplete="off"
              autoCapitalize="characters"
              spellCheck={false}
              maxLength={32}
            />
            <p className="field-hint" id="promo-hint">
              Если у вас есть код, введите его до оплаты. Код действует только на выбранный
              тариф и только на одну покупку.
            </p>
          </div>
          <div className="field field-consent">
            <label className="consent-label" htmlFor="purchase-consent">
              <input
                id="purchase-consent"
                name="consent"
                type="checkbox"
                checked={consent}
                onChange={(event) => setConsent(event.target.checked)}
                required
              />
              <span>
                Я принимаю условия{" "}
                <Link href="/oferta" target="_blank" rel="noopener noreferrer">
                  Публичной оферты
                </Link>{" "}
                и{" "}
                <Link href="/privacy" target="_blank" rel="noopener noreferrer">
                  Политики конфиденциальности
                </Link>
                , в том числе правила отмены, переноса и возврата.
              </span>
            </label>
          </div>
          <button
            className="button"
            type="submit"
            disabled={pending || !slotId || !offerId || !consent || emailVerificationRequired}
          >
            {isAuthenticated ? "Перейти к оплате" : "Войти и оплатить"}
          </button>
          <p className="booking-note">
            Оплата через ЮKassa. Выбранный слот закрепляется за вами на время оплаты;
            занятие подтвердится после поступления платежа.
          </p>
        </form>
      )}

      {!isPackageMode && !isRescheduleMode && availablePackages.length > 0 ? (
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
                  disabled={pending || !slotId || emailVerificationRequired}
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
