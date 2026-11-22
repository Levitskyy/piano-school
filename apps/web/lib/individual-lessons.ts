import { API_URL, fetchWithSession } from "@/lib/auth";
import type {
  AccountIndividualLessons,
  IndividualLessonOffer,
  LessonSlot,
} from "@/lib/individual-lessons-shared";

export * from "@/lib/individual-lessons-shared";

export async function getIndividualLessonOffers(): Promise<IndividualLessonOffer[]> {
  try {
    const response = await fetch(`${API_URL}/individual-lessons/offers`, {
      cache: "no-store",
    });
    if (!response.ok) return [];
    return (await response.json()) as IndividualLessonOffer[];
  } catch {
    return [];
  }
}

export async function getFreeLessonSlots(
  excludeBookingId?: string,
): Promise<LessonSlot[]> {
  try {
    const query = excludeBookingId
      ? `?exclude_booking=${encodeURIComponent(excludeBookingId)}`
      : "";
    const response = await fetchWithSession(`/individual-lessons/slots${query}`);
    if (!response.ok) return [];
    return (await response.json()) as LessonSlot[];
  } catch {
    return [];
  }
}

export async function getAccountIndividualLessons(): Promise<AccountIndividualLessons> {
  const empty: AccountIndividualLessons = { packages: [], bookings: [] };
  try {
    const response = await fetchWithSession("/individual-lessons/account");
    if (!response.ok) return empty;
    return (await response.json()) as AccountIndividualLessons;
  } catch {
    return empty;
  }
}
