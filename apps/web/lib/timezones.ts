export type TimezoneGroup = {
  label: string;
  zones: string[];
};

const cityNames: Record<string, string> = {
  "Europe/Kaliningrad": "Калининград",
  "Europe/Moscow": "Москва",
  "Europe/Yekaterinburg": "Екатеринбург",
  "Asia/Novosibirsk": "Новосибирск",
  "Asia/Irkutsk": "Иркутск",
  "Asia/Vladivostok": "Владивосток",
  "Asia/Kamchatka": "Петропавловск-Камчатский",
  "Europe/Kyiv": "Киев",
  "Europe/Minsk": "Минск",
  "Asia/Almaty": "Алматы",
  "Asia/Tashkent": "Ташкент",
  "Asia/Bishkek": "Бишкек",
  "Asia/Tbilisi": "Тбилиси",
  "Asia/Yerevan": "Ереван",
  "Europe/London": "Лондон",
  "Europe/Berlin": "Берлин",
  "Europe/Paris": "Париж",
  "Europe/Madrid": "Мадрид",
  "Europe/Warsaw": "Варшава",
  "Europe/Istanbul": "Стамбул",
  "Asia/Dubai": "Дубай",
  "Asia/Tehran": "Тегеран",
  "Asia/Kolkata": "Дели",
  "Asia/Bangkok": "Бангкок",
  "Asia/Singapore": "Сингапур",
  "Asia/Shanghai": "Шанхай",
  "Asia/Tokyo": "Токио",
  "Asia/Seoul": "Сеул",
  "America/New_York": "Нью-Йорк",
  "America/Chicago": "Чикаго",
  "America/Los_Angeles": "Лос-Анджелес",
  "America/Toronto": "Торонто",
  "America/Sao_Paulo": "Сан-Паулу",
  "Australia/Sydney": "Сидней",
  "Pacific/Auckland": "Окленд",
  "Etc/UTC": "UTC",
};

export const timezoneGroups: TimezoneGroup[] = [
  {
    label: "Россия и соседние страны",
    zones: [
      "Europe/Kaliningrad",
      "Europe/Moscow",
      "Europe/Yekaterinburg",
      "Asia/Novosibirsk",
      "Asia/Irkutsk",
      "Asia/Vladivostok",
      "Asia/Kamchatka",
      "Europe/Kyiv",
      "Europe/Minsk",
      "Asia/Almaty",
      "Asia/Tashkent",
      "Asia/Bishkek",
      "Asia/Tbilisi",
      "Asia/Yerevan",
    ],
  },
  {
    label: "Европа",
    zones: [
      "Europe/London",
      "Europe/Berlin",
      "Europe/Paris",
      "Europe/Madrid",
      "Europe/Warsaw",
      "Europe/Istanbul",
    ],
  },
  {
    label: "Азия",
    zones: [
      "Asia/Dubai",
      "Asia/Tehran",
      "Asia/Kolkata",
      "Asia/Bangkok",
      "Asia/Singapore",
      "Asia/Shanghai",
      "Asia/Tokyo",
      "Asia/Seoul",
    ],
  },
  {
    label: "Америка",
    zones: [
      "America/New_York",
      "America/Chicago",
      "America/Los_Angeles",
      "America/Toronto",
      "America/Sao_Paulo",
    ],
  },
  {
    label: "Другое",
    zones: ["Australia/Sydney", "Pacific/Auckland", "Etc/UTC"],
  },
];

export function getTimezoneGroup(timeZone: string): string {
  return (
    timezoneGroups.find((group) => group.zones.includes(timeZone))?.label ?? "Другое"
  );
}

export function getTimezoneLabel(timeZone: string): string {
  if (cityNames[timeZone]) return cityNames[timeZone];
  return (timeZone.split("/").at(-1) ?? timeZone).replace(/_/g, " ");
}

export function getTimezoneOffset(timeZone: string, date: Date): string {
  try {
    const parts = new Intl.DateTimeFormat("ru-RU", {
      timeZone,
      timeZoneName: "shortOffset",
    }).formatToParts(date);
    const value = parts.find((part) => part.type === "timeZoneName")?.value;
    return !value || value === "GMT" ? "GMT+0" : value;
  } catch {
    return "";
  }
}

export function formatTimeInTimezone(timeZone: string, date: Date): string {
  try {
    return new Intl.DateTimeFormat("ru-RU", {
      timeZone,
      day: "numeric",
      month: "long",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  } catch {
    return "";
  }
}

export function detectBrowserTimezone(): string | null {
  try {
    const zone = new Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (!zone) return null;
    return /^[A-Za-z_+\-/]+$/.test(zone) ? zone : null;
  } catch {
    return null;
  }
}
