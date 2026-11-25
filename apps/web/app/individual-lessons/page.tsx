import type { Metadata } from "next";

import { IndividualLessonBooking } from "@/components/individual-lesson-booking";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { getCurrentUser } from "@/lib/auth";
import {
  getAccountIndividualLessons,
  getFreeLessonSlots,
  getIndividualLessonOffers,
} from "@/lib/individual-lessons";

export const metadata: Metadata = {
  title: "Индивидуальные занятия",
  description:
    "Разовые уроки и пакеты занятий с выбором удобного времени в вашем часовом поясе.",
};

export default async function IndividualLessonsPage() {
  const [offers, slots, user] = await Promise.all([
    getIndividualLessonOffers(),
    getFreeLessonSlots(),
    getCurrentUser(),
  ]);
  const account = user ? await getAccountIndividualLessons() : { packages: [] };

  return (
    <div className="site">
      <SiteHeader />

      <main>
        <section className="section lesson-booking-hero">
          <p className="eyebrow">Живые занятия</p>
          <h1 id="main-heading" tabIndex={-1}>
            Индивидуальные уроки
          </h1>
          <p className="lead">
            Один урок или пакет занятий — выберите удобный слот в своём часовом поясе.
            Ссылка на встречу появится в кабинете после подтверждения.
          </p>
        </section>

        <section
          className="section lesson-booking-section"
          aria-labelledby="booking-title"
        >
          <div className="section-head">
            <h2 id="booking-title" className="visually-hidden">
              Выбор занятия
            </h2>
          </div>
          <IndividualLessonBooking
            offers={offers}
            slots={slots}
            packages={account.packages}
            isAuthenticated={Boolean(user)}
            emailVerificationRequired={Boolean(user && !user.email_verified_at)}
            timeZoneOverride={user?.timezone ?? null}
          />
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
