export type IndividualLessonOffer = {
  id: string;
  slug: string;
  title: string;
  description: string;
  kind: "single" | "package" | string;
  lessons_count: number;
  duration_minutes: number;
  price_minor: number | null;
  currency: string;
  validity_days: number | null;
};

export type LessonSlot = {
  id: string;
  starts_at: string;
  ends_at: string;
  duration_minutes: number;
};

export type LessonPackage = {
  id: string;
  offer_slug: string;
  offer_title: string;
  total_lessons: number;
  remaining_lessons: number;
  status: string;
  expires_at: string | null;
  created_at: string;
};

export type LessonBooking = {
  id: string;
  package_id: string;
  offer_title: string;
  status: string;
  starts_at: string;
  ends_at: string;
  meeting_url: string | null;
  created_at: string;
};

export type AccountIndividualLessons = {
  packages: LessonPackage[];
  bookings: LessonBooking[];
};

const statusLabels: Record<string, string> = {
  active: "активен",
  exhausted: "исчерпан",
  expired: "истёк",
  cancelled: "отменён",
  confirmed: "подтверждено",
  completed: "завершено",
  in_progress: "в работе",
  pending: "ожидает",
};

export function formatStatusLabel(status: string): string {
  return statusLabels[status] ?? status;
}

export function formatIndividualLessonPrice(offer: IndividualLessonOffer): string {
  if (offer.price_minor === null) return "Цена уточняется";
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: offer.currency || "RUB",
    maximumFractionDigits: 0,
  }).format(offer.price_minor / 100);
}

export function formatSlotDateTime(value: string, timeZone: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    timeZone,
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function formatSlotDay(value: string, timeZone: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    timeZone,
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(new Date(value));
}

export function formatSlotTime(value: string, timeZone: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    timeZone,
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function formatCalendarWeekday(value: string, timeZone: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    timeZone,
    weekday: "short",
  }).format(new Date(value));
}

export function formatCalendarDate(value: string, timeZone: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    timeZone,
    day: "numeric",
    month: "short",
  }).format(new Date(value));
}
