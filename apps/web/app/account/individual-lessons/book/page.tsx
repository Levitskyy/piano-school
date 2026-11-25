import type { Metadata } from "next";
import Link from "next/link";
import { ClientRedirect } from "@/components/client-redirect";
import { IndividualLessonBooking } from "@/components/individual-lesson-booking";
import { EmptyState } from "@/components/empty-state";
import { getCurrentUser } from "@/lib/auth";
import { getAccountIndividualLessons, getFreeLessonSlots } from "@/lib/individual-lessons";

export const metadata: Metadata = {
  title: "Запись на урок",
};

type BookLessonPageProps = {
  searchParams: Promise<{ package?: string | string[] }>;
};

export default async function BookLessonPage({ searchParams }: BookLessonPageProps) {
  const user = await getCurrentUser();
  if (!user) return <ClientRedirect to="/login?next=/account/individual-lessons" />;

  const params = await searchParams;
  const packageId = typeof params.package === "string" ? params.package : undefined;

  const [account, slots] = await Promise.all([
    getAccountIndividualLessons(),
    getFreeLessonSlots(),
  ]);

  const bookingPackage = account.packages.find(
    (item) =>
      item.id === packageId &&
      item.status === "active" &&
      item.remaining_lessons > 0,
  );

  if (!bookingPackage) {
    return (
      <div className="panel-page">
        <header className="panel-page-head">
          <p className="eyebrow">Расписание</p>
          <h1>Запись на урок</h1>
        </header>
        <EmptyState
          title="Пакет недоступен"
          text="Похоже, у этого пакета закончились занятия или он вам не принадлежит. Вернитесь к списку занятий."
          action={
            <Link className="button" href="/account/individual-lessons">
              К индивидуальным занятиям
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Расписание</p>
        <h1>Запись на урок</h1>
        <p className="panel-lead">
          Выберите удобный слот — занятие спишется из пакета сразу после
          подтверждения.
        </p>
      </header>

      <section className="account-section" aria-labelledby="booking-title">
        <div className="panel-section-head">
          <h2 id="booking-title" className="visually-hidden">
            Выбор времени
          </h2>
        </div>
        <IndividualLessonBooking
          offers={[]}
          slots={slots}
          packages={[]}
          isAuthenticated
          emailVerificationRequired={!user.email_verified_at}
          bookingPackage={bookingPackage}
          timeZoneOverride={user.timezone}
        />
      </section>
    </div>
  );
}
