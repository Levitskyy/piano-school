export type TimezoneOption = {
  value: string;
  label: string;
  group: string;
};

const cityNames: Record<string, string> = {
  "Europe/Moscow": "Москва",
  "Europe/Kaliningrad": "Калининград",
  "Europe/Samara": "Самара",
  "Europe/Yekaterinburg": "Екатеринбург",
  "Asia/Yekaterinburg": "Екатеринбург",
  "Asia/Omsk": "Омск",
  "Asia/Novosibirsk": "Новосибирск",
  "Asia/Barnaul": "Барнаул",
  "Asia/Tomsk": "Томск",
  "Asia/Novokuznetsk": "Новокузнецк",
  "Asia/Krasnoyarsk": "Красноярск",
  "Asia/Irkutsk": "Иркутск",
  "Asia/Yakutsk": "Якутск",
  "Asia/Vladivostok": "Владивосток",
  "Asia/Sakhalin": "Южно-Сахалинск",
  "Asia/Magadan": "Магадан",
  "Asia/Kamchatka": "Петропавловск-Камчатский",
  "Asia/Anadyr": "Анадырь",
  "Europe/Kyiv": "Киев",
  "Europe/Kiev": "Киев",
  "Europe/Minsk": "Минск",
  "Europe/Chisinau": "Кишинёв",
  "Europe/Simferopol": "Симферополь",
  "Asia/Almaty": "Алматы",
  "Asia/Tashkent": "Ташкент",
  "Asia/Bishkek": "Бишкек",
  "Asia/Tbilisi": "Тбилиси",
  "Asia/Yerevan": "Ереван",
  "Asia/Baku": "Баку",
  "Asia/Dushanbe": "Душанбе",
  "Asia/Ashgabat": "Ашхабад",
  "Europe/London": "Лондон",
  "Europe/Dublin": "Дублин",
  "Europe/Lisbon": "Лиссабон",
  "Europe/Madrid": "Мадрид",
  "Europe/Paris": "Париж",
  "Europe/Berlin": "Берлин",
  "Europe/Amsterdam": "Амстердам",
  "Europe/Brussels": "Брюссель",
  "Europe/Zurich": "Цюрих",
  "Europe/Vienna": "Вена",
  "Europe/Rome": "Рим",
  "Europe/Stockholm": "Стокгольм",
  "Europe/Oslo": "Осло",
  "Europe/Copenhagen": "Копенгаген",
  "Europe/Helsinki": "Хельсинки",
  "Europe/Warsaw": "Варшава",
  "Europe/Prague": "Прага",
  "Europe/Budapest": "Будапешт",
  "Europe/Bucharest": "Бухарест",
  "Europe/Sofia": "София",
  "Europe/Athens": "Афины",
  "Europe/Istanbul": "Стамбул",
  "Europe/Belgrade": "Белград",
  "Europe/Zagreb": "Загреб",
  "Europe/Ljubljana": "Любляна",
  "Europe/Bratislava": "Братислава",
  "Europe/Vilnius": "Вильнюс",
  "Europe/Riga": "Рига",
  "Europe/Tallinn": "Таллин",
  "Asia/Dubai": "Дубай",
  "Asia/Riyadh": "Эр-Рияд",
  "Asia/Tehran": "Тегеран",
  "Asia/Jerusalem": "Иерусалим",
  "Asia/Beirut": "Бейрут",
  "Asia/Kolkata": "Дели",
  "Asia/Calcutta": "Калькутта",
  "Asia/Colombo": "Коломбо",
  "Asia/Dhaka": "Дакка",
  "Asia/Kathmandu": "Катманду",
  "Asia/Bangkok": "Бангкок",
  "Asia/Ho_Chi_Minh": "Хошимин",
  "Asia/Singapore": "Сингапур",
  "Asia/Kuala_Lumpur": "Куала-Лумпур",
  "Asia/Jakarta": "Джакарта",
  "Asia/Manila": "Манила",
  "Asia/Shanghai": "Шанхай",
  "Asia/Hong_Kong": "Гонконг",
  "Asia/Taipei": "Тайбэй",
  "Asia/Seoul": "Сеул",
  "Asia/Tokyo": "Токио",
  "America/New_York": "Нью-Йорк",
  "America/Chicago": "Чикаго",
  "America/Denver": "Денвер",
  "America/Los_Angeles": "Лос-Анджелес",
  "America/Toronto": "Торонто",
  "America/Vancouver": "Ванкувер",
  "America/Mexico_City": "Мехико",
  "America/Sao_Paulo": "Сан-Паулу",
  "America/Argentina/Buenos_Aires": "Буэнос-Айрес",
  "America/Santiago": "Сантьяго",
  "America/Bogota": "Богота",
  "America/Lima": "Лима",
  "Australia/Sydney": "Сидней",
  "Australia/Melbourne": "Мельбурн",
  "Australia/Brisbane": "Брисбен",
  "Australia/Perth": "Перт",
  "Pacific/Auckland": "Окленд",
  "Pacific/Honolulu": "Гонолулу",
  "Africa/Cairo": "Каир",
  "Africa/Johannesburg": "Йоханнесбург",
  "Africa/Lagos": "Лагос",
  "Africa/Nairobi": "Найроби",
  "Etc/UTC": "UTC",
  UTC: "UTC",
};

const cisZones = new Set([
  "Europe/Moscow",
  "Europe/Kaliningrad",
  "Europe/Samara",
  "Europe/Yekaterinburg",
  "Europe/Kyiv",
  "Europe/Kiev",
  "Europe/Minsk",
  "Europe/Chisinau",
  "Europe/Simferopol",
  "Asia/Yekaterinburg",
  "Asia/Omsk",
  "Asia/Novosibirsk",
  "Asia/Barnaul",
  "Asia/Tomsk",
  "Asia/Novokuznetsk",
  "Asia/Krasnoyarsk",
  "Asia/Irkutsk",
  "Asia/Yakutsk",
  "Asia/Vladivostok",
  "Asia/Sakhalin",
  "Asia/Magadan",
  "Asia/Kamchatka",
  "Asia/Anadyr",
  "Asia/Almaty",
  "Asia/Tashkent",
  "Asia/Bishkek",
  "Asia/Tbilisi",
  "Asia/Yerevan",
  "Asia/Baku",
  "Asia/Dushanbe",
  "Asia/Ashgabat",
]);

const groupByPrefix: Record<string, string> = {
  Europe: "Европа",
  Asia: "Азия",
  America: "Америка",
  Africa: "Африка",
  Australia: "Австралия и Океания",
  Pacific: "Австралия и Океания",
};

const groupOrder = [
  "Россия и соседние страны",
  "Европа",
  "Азия",
  "Америка",
  "Африка",
  "Австралия и Океания",
  "Прочее",
];

type IntlWithSupportedValues = typeof Intl & {
  supportedValuesOf?: (key: "timeZone") => string[];
};

function supportedZones(): string[] {
  const intl = Intl as IntlWithSupportedValues;
  if (typeof intl.supportedValuesOf === "function") {
    return intl.supportedValuesOf("timeZone");
  }
  return Array.from(new Set(Object.keys(cityNames)));
}

export function getTimezoneGroup(timeZone: string): string {
  if (cisZones.has(timeZone)) return "Россия и соседние страны";
  return groupByPrefix[timeZone.split("/")[0]] ?? "Прочее";
}

export function getTimezoneLabel(timeZone: string): string {
  if (cityNames[timeZone]) return cityNames[timeZone];
  const tail = timeZone.split("/").at(-1) ?? timeZone;
  return tail.replace(/_/g, " ");
}

export function getTimezoneOffset(timeZone: string, date: Date): string {
  try {
    const options = { timeZone, timeZoneName: "shortOffset" } as const;
    let parts = new Intl.DateTimeFormat("ru-RU", options).formatToParts(date);
    let value = parts.find((part) => part.type === "timeZoneName")?.value;

    if (!value || value === "GMT") {
      parts = new Intl.DateTimeFormat("ru-RU", {
        timeZone,
        timeZoneName: "short",
      }).formatToParts(date);
      value = parts.find((part) => part.type === "timeZoneName")?.value;
    }

    if (!value || value === "GMT") return "GMT+0";
    return value;
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

export function getTimezoneOptions(): TimezoneOption[] {
  return supportedZones()
    .map((value) => ({
      value,
      label: `${getTimezoneLabel(value)} (${getTimezoneOffset(value, new Date())})`,
      group: getTimezoneGroup(value),
    }))
    .sort((a, b) => a.label.localeCompare(b.label, "ru"));
}

export function groupTimezoneOptions(options: TimezoneOption[]): TimezoneOption[][] {
  return groupOrder.map((group) => options.filter((option) => option.group === group));
}

export const timezoneGroupOrder = groupOrder;
