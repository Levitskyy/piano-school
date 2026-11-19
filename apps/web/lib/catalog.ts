import { API_URL, fetchWithSession } from "@/lib/auth";

export type CourseOffer = {
  id: string;
  slug: string;
  title: string;
  description: string;
  kind: "self_study" | "with_mentorship" | string;
  price_minor: number | null;
  currency: string;
  mentorship_days: number | null;
  is_active: boolean;
};

export type LessonSummary = {
  id: string;
  slug: string;
  title: string;
  description: string;
  position: number;
  duration_seconds: number | null;
};

export type CourseModule = {
  id: string;
  title: string;
  description: string;
  position: number;
  lessons: LessonSummary[];
};

export type CourseSummary = {
  id: string;
  slug: string;
  title: string;
  subtitle: string | null;
  description: string;
  level: string;
  cover_url: string | null;
  offers: CourseOffer[];
};

export type CourseDetail = CourseSummary & {
  modules: CourseModule[];
};

export type CourseAccess = {
  id: string;
  source: string;
  starts_at: string;
  expires_at: string | null;
  mentorship_ends_at: string | null;
  offer: CourseOffer | null;
};

export type AccountCourse = {
  access: CourseAccess;
  course: CourseSummary;
  completed_lessons: number;
  total_lessons: number;
};

export type Progress = {
  status: "not_started" | "in_progress" | "completed" | string;
  last_position_seconds: number;
  completed_at: string | null;
};

export type LessonDetail = {
  id: string;
  slug: string;
  title: string;
  description: string;
  duration_seconds: number | null;
  module_title: string;
  course_slug: string;
  course_title: string;
  materials: Array<{
    id: string;
    title: string;
    kind: string;
    url: string | null;
  }>;
  progress: Progress | null;
};

export async function getPublicCourses(): Promise<CourseSummary[]> {
  try {
    const response = await fetch(`${API_URL}/courses`, { cache: "no-store" });
    if (!response.ok) return [];
    return (await response.json()) as CourseSummary[];
  } catch {
    return [];
  }
}

export async function getPublicCourse(slug: string): Promise<CourseDetail | null> {
  try {
    const response = await fetch(`${API_URL}/courses/${encodeURIComponent(slug)}`, {
      cache: "no-store",
    });
    if (!response.ok) return null;
    return (await response.json()) as CourseDetail;
  } catch {
    return null;
  }
}

export async function getAccountCourses(): Promise<AccountCourse[]> {
  try {
    const response = await fetchWithSession("/account/courses");
    if (!response.ok) return [];
    return (await response.json()) as AccountCourse[];
  } catch {
    return [];
  }
}

export function formatPrice(offer: CourseOffer): string {
  if (offer.price_minor === null) return "Цена уточняется";
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: offer.currency,
    maximumFractionDigits: 0,
  }).format(offer.price_minor / 100);
}

export function formatDate(value: string | null): string {
  if (!value) return "";
  return new Intl.DateTimeFormat("ru-RU", { dateStyle: "medium" }).format(
    new Date(value),
  );
}

export function formatDuration(seconds: number | null): string {
  if (!seconds) return "Видео готовится";
  const minutes = Math.round(seconds / 60);
  return `${minutes} мин`;
}

export function levelLabel(level: string): string {
  const labels: Record<string, string> = {
    beginner: "С нуля",
    intermediate: "Средний уровень",
    advanced: "Продвинутый",
  };
  return labels[level] ?? level;
}
