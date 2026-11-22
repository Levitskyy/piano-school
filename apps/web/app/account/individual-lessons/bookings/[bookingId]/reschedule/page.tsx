import type { Metadata } from "next";
import Link from "next/link";

import { ClientRedirect } from "@/components/client-redirect";
import { EmptyState } from "@/components/empty-state";
import { IndividualLessonBooking } from "@/components/individual-lesson-booking";
import { getCurrentUser } from "@/lib/auth";
import {
  getAccountIndividualLessons,
  getFreeLessonSlots,
} from "@/lib/individual-lessons";

export const metadata: Metadata = {
  title: "Перенос занятия",
};

type RescheduleLessonPageProps = {
  params: Promise<{ bookingId: string }>;
};

export default async function RescheduleLessonPage({
  params,
}: RescheduleLessonPageProps) {
  const { bookingId } = await params;
  const user = await getCurrentUser();
  if (!user) {
    const next = `/account/individual-lessons/bookings/${bookingId}/reschedule`;
    return <ClientRedirect to={`/login?next=${encodeURIComponent(next)}`} />;
  }

  const account = await getAccountIndividualLessons();
  const booking = account.bookings.find((item) => item.id === bookingId);

  if (!booking) {
    return (
      <div className="panel-page">
        <header className="panel-page-head">
          <p className="eyebrow">Расписание</p>
          <h1>Перенос занятия</h1>
        </header>
        <EmptyState
          title="Запись не найдена"
          text="Возможно, занятие уже отменено или ссылка устарела."
          action={
            <Link className="button" href="/account/individual-lessons">
              К индивидуальным занятиям
            </Link>
          }
        />
      </div>
    );
  }

  if (booking.status !== "confirmed" || !booking.can_change) {
    return (
      <div className="panel-page">
        <header className="panel-page-head">
          <p className="eyebrow">Расписание</p>
          <h1>Перенос занятия</h1>
        </header>
        <EmptyState
          title="Перенести занятие нельзя"
          text="Занятие уже началось, отменено или до него осталось слишком мало времени. Напишите преподавателю."
          action={
            <Link className="button" href="/account/individual-lessons">
              К индивидуальным занятиям
            </Link>
          }
        />
      </div>
    );
  }

  const slots = await getFreeLessonSlots(booking.id);

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Расписание</p>
        <h1>Перенос занятия</h1>
        <p className="panel-lead">
          Выберите новое время. Старый слот освободится, а занятие останется в
          том же пакете. Время указано в вашем часовом поясе ({user.timezone}).
        </p>
      </header>

      <section className="account-section" aria-labelledby="reschedule-title">
        <div className="panel-section-head">
          <h2 id="reschedule-title" className="visually-hidden">
            Новое время занятия
          </h2>
        </div>
        <IndividualLessonBooking
          offers={[]}
          slots={slots}
          packages={[]}
          isAuthenticated
          rescheduleBooking={booking}
          timeZoneOverride={user.timezone}
        />
      </section>
    </div>
  );
}
