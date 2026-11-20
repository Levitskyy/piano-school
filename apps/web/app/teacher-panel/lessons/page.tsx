import type { Metadata } from "next";
import { ClientRedirect } from "@/components/client-redirect";
import { TeacherLessonBookingList } from "@/components/teacher-lessons";
import { getCurrentUser } from "@/lib/auth";
import { getTeacherLessons } from "@/lib/teacher";

export const metadata: Metadata = {
  title: "Занятия",
};

export default async function TeacherLessonsPage() {
  const user = await getCurrentUser();
  if (!user) return <ClientRedirect to="/login?next=/teacher-panel/lessons" />;
  if (user.role === "student") return <ClientRedirect to="/account" />;

  const bookings = await getTeacherLessons();
  const now = new Date();
  const upcoming = bookings.filter(
    (item) => new Date(item.starts_at) > now && item.status !== "cancelled",
  );
  const past = bookings.filter(
    (item) => new Date(item.starts_at) <= now || item.status === "cancelled",
  );

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Преподаватель</p>
        <h1>Занятия</h1>
        <p className="panel-lead">
          Все записи учеников и ссылки на встречи. Время указано в вашем часовом
          поясе ({user.timezone}).
        </p>
      </header>

      <section className="account-section" aria-labelledby="upcoming-lessons-title">
        <div className="panel-section-head">
          <h2 id="upcoming-lessons-title">Предстоящие занятия</h2>
        </div>
        <TeacherLessonBookingList
          bookings={upcoming}
          timeZone={user.timezone}
          emptyTitle="Записей пока нет"
          emptyText="Когда ученик выберет время, занятие появится здесь."
        />
      </section>

      {past.length > 0 ? (
        <section className="account-section" aria-labelledby="past-lessons-title">
          <div className="panel-section-head">
            <h2 id="past-lessons-title">История занятий</h2>
          </div>
          <TeacherLessonBookingList
            bookings={past}
            timeZone={user.timezone}
            emptyTitle="История пуста"
            emptyText="Прошедшие занятия появятся здесь."
          />
        </section>
      ) : null}
    </div>
  );
}
