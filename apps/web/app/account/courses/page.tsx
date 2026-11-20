import type { Metadata } from "next";
import Link from "next/link";
import { ClientRedirect } from "@/components/client-redirect";
import { EmptyState } from "@/components/empty-state";
import { getCurrentUser } from "@/lib/auth";
import { formatDate, getAccountCourses } from "@/lib/catalog";

export const metadata: Metadata = {
  title: "Мои курсы",
};

export default async function AccountCoursesPage() {
  const user = await getCurrentUser();
  if (!user) return <ClientRedirect to="/login?next=/account/courses" />;

  const courses = await getAccountCourses();

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Обучение</p>
        <h1>Мои курсы</h1>
        <p className="panel-lead">
          Здесь собраны курсы, к которым у вас есть доступ. Прогресс сохраняется по
          каждому уроку.
        </p>
      </header>

      {courses.length === 0 ? (
        <EmptyState
          title="Пока нет активного курса"
          text="Выберите курс и вариант покупки. После подтверждения оплаты доступ появится здесь автоматически."
          action={
            <Link className="button" href="/courses">
              Открыть каталог
            </Link>
          }
        />
      ) : (
        <div className="account-course-list">
          {courses.map((item) => {
            const percent =
              item.total_lessons > 0
                ? Math.round((item.completed_lessons / item.total_lessons) * 100)
                : 0;

            return (
              <article className="account-course" key={item.access.id}>
                <div className="account-course-head">
                  <div>
                    <p className="card-meta">
                      {item.access.offer?.title ?? "Доступ к курсу"}
                    </p>
                    <h2>{item.course.title}</h2>
                    {item.course.subtitle ? <p>{item.course.subtitle}</p> : null}
                  </div>
                  <Link
                    className="button button-small"
                    href={`/account/courses/${item.course.slug}`}
                  >
                    Открыть
                  </Link>
                </div>

                <div className="progress-row">
                  <div
                    className="progress-track"
                    role="progressbar"
                    aria-valuemin={0}
                    aria-valuemax={item.total_lessons}
                    aria-valuenow={item.completed_lessons}
                    aria-label="Пройдено уроков"
                  >
                    <span style={{ inlineSize: `${percent}%` }} />
                  </div>
                  <span>
                    {item.completed_lessons} из {item.total_lessons} уроков
                  </span>
                </div>

                <div className="account-course-meta">
                  <span>Доступ с {formatDate(item.access.starts_at)}</span>
                  {item.access.mentorship_ends_at ? (
                    <span>
                      Сопровождение до {formatDate(item.access.mentorship_ends_at)}
                    </span>
                  ) : (
                    <span>Без сопровождения</span>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}

      <section className="account-section" aria-labelledby="homework-title">
        <div className="panel-section-head">
          <h2 id="homework-title">Домашние задания</h2>
        </div>
        <EmptyState
          title="Раздел готовится"
          text="Загрузка файлов и комментарии преподавателя появятся внутри этого экрана, рядом с курсом и уроком."
        />
      </section>

      <section className="account-section" aria-labelledby="mentorship-title">
        <div className="panel-section-head">
          <h2 id="mentorship-title">Сопровождение</h2>
        </div>
        <EmptyState
          title="Раздел готовится"
          text="Статус периода сопровождения, загрузка работ и ответы преподавателя будут показаны здесь, внутри «Мои курсы»."
        />
      </section>
    </div>
  );
}
