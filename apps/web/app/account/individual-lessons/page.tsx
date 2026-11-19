import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { EmptyState } from "@/components/empty-state";
import { getCurrentUser } from "@/lib/auth";
import { formatSlotDateTime } from "@/lib/individual-lessons-shared";
import { getAccountIndividualLessons } from "@/lib/individual-lessons";

export const metadata: Metadata = {
  title: "Индивидуальные занятия",
};

export default async function AccountIndividualLessonsPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/account/individual-lessons");

  const account = await getAccountIndividualLessons();
  const now = new Date();
  const upcoming = account.bookings.filter(
    (item) => new Date(item.starts_at) > now && item.status !== "cancelled",
  );
  const past = account.bookings.filter(
    (item) => new Date(item.starts_at) <= now || item.status === "cancelled",
  );
  const activePackages = account.packages.filter(
    (item) => item.status === "active" && item.remaining_lessons > 0,
  );

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Расписание</p>
        <h1>Индивидуальные занятия</h1>
        <p className="panel-lead">
          Купленные уроки, остаток по пакетам и ближайшие записи. Время указано в
          вашем часовом поясе ({user.timezone}).
        </p>
      </header>

      {account.packages.length > 0 ? (
        <section className="account-section" aria-labelledby="packages-title">
          <div className="panel-section-head">
            <h2 id="packages-title">Пакеты и уроки</h2>
          </div>
          <div className="account-course-list">
            {account.packages.map((item) => (
              <article className="account-course" key={item.id}>
                <div className="account-course-head">
                  <div>
                    <p className="card-meta">{item.offer_title}</p>
                    <h3>
                      Осталось {item.remaining_lessons} из {item.total_lessons} занятий
                    </h3>
                  </div>
                  <span className="status-pill">{item.status}</span>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <section className="account-section" aria-labelledby="upcoming-title">
        <div className="panel-section-head">
          <h2 id="upcoming-title">Предстоящие занятия</h2>
        </div>
        {upcoming.length === 0 ? (
          <EmptyState
            title="Записей пока нет"
            text="Выберите удобный слот — он появится здесь сразу после покупки."
            action={
              <Link className="button" href="/individual-lessons">
                Выбрать время
              </Link>
            }
          />
        ) : (
          <ul className="booking-list">
            {upcoming.map((item) => (
              <li className="booking-item" key={item.id}>
                <div>
                  <h3>{item.offer_title}</h3>
                  <p>{formatSlotDateTime(item.starts_at, user.timezone)}</p>
                  {item.meeting_url ? (
                    <a href={item.meeting_url} target="_blank" rel="noreferrer">
                      Ссылка на встречу
                    </a>
                  ) : (
                    <p className="body-text">
                      Ссылка на встречу будет добавлена преподавателем.
                    </p>
                  )}
                </div>
                <span className="status-pill">{item.status}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {activePackages.length > 0 ? (
        <section className="account-section">
          <p className="body-text">
            Остались занятия в пакете?{" "}
            <Link href="/individual-lessons">Запишитесь на следующий слот</Link>.
          </p>
        </section>
      ) : null}

      {past.length > 0 ? (
        <section className="account-section" aria-labelledby="past-title">
          <div className="panel-section-head">
            <h2 id="past-title">История занятий</h2>
          </div>
          <ul className="booking-list">
            {past.map((item) => (
              <li className="booking-item" key={item.id}>
                <div>
                  <h3>{item.offer_title}</h3>
                  <p>{formatSlotDateTime(item.starts_at, user.timezone)}</p>
                </div>
                <span className="status-pill">{item.status}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
