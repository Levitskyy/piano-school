import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ClientRedirect } from "@/components/client-redirect";
import { EmptyState } from "@/components/empty-state";
import { getCurrentUser } from "@/lib/auth";
import { formatDate, formatDuration, getAccountCourses, getPublicCourse } from "@/lib/catalog";

type AccountCoursePageProps = {
  params: Promise<{ slug: string }>;
};

export async function generateMetadata({
  params,
}: AccountCoursePageProps): Promise<Metadata> {
  const { slug } = await params;
  const course = await getPublicCourse(slug);
  return { title: course?.title ?? "Курс не найден" };
}

export default async function AccountCoursePage({ params }: AccountCoursePageProps) {
  const { slug } = await params;
  const user = await getCurrentUser();
  if (!user) return <ClientRedirect to={`/login?next=/account/courses/${slug}`} />;

  const [course, accountCourses] = await Promise.all([
    getPublicCourse(slug),
    getAccountCourses(),
  ]);
  if (!course) notFound();

  const item = accountCourses.find((entry) => entry.course.slug === course.slug);
  if (!item) {
    return (
      <div className="panel-page">
        <header className="panel-page-head">
          <p className="eyebrow">Мои курсы</p>
          <h1>{course.title}</h1>
        </header>
        <EmptyState
          title="Нет доступа к курсу"
          text="Этот курс не открыт в вашем кабинете. После покупки доступ появится здесь автоматически."
          action={
            <Link className="button" href={`/courses/${course.slug}`}>
              Посмотреть курс
            </Link>
          }
        />
      </div>
    );
  }

  const totalLessons = course.modules.reduce(
    (total, module) => total + module.lessons.length,
    0,
  );
  const percent =
    totalLessons > 0
      ? Math.round((item.completed_lessons / totalLessons) * 100)
      : 0;

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <Link className="back-link" href="/account/courses">
          ← Мои курсы
        </Link>
        <p className="eyebrow">{item.access.offer?.title ?? "Доступ к курсу"}</p>
        <h1>{course.title}</h1>
        {course.subtitle ? <p className="panel-lead">{course.subtitle}</p> : null}
        <div className="account-course-meta">
          <span>Доступ с {formatDate(item.access.starts_at)}</span>
          {item.access.mentorship_ends_at ? (
            <span>Сопровождение до {formatDate(item.access.mentorship_ends_at)}</span>
          ) : (
            <span>Без сопровождения</span>
          )}
        </div>
        <div className="progress-row">
          <div
            className="progress-track"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={totalLessons}
            aria-valuenow={item.completed_lessons}
            aria-label="Пройдено уроков"
          >
            <span style={{ inlineSize: `${percent}%` }} />
          </div>
          <span>
            {item.completed_lessons} из {totalLessons} уроков
          </span>
        </div>
      </header>

      <section className="account-section" aria-labelledby="course-content-title">
        <div className="panel-section-head">
          <h2 id="course-content-title">Содержание курса</h2>
        </div>
        <ol className="course-program">
          {course.modules.map((module, index) => (
            <li key={module.id}>
              <div className="course-module-head">
                <span className="module-number">{String(index + 1).padStart(2, "0")}</span>
                <div>
                  <h3>{module.title}</h3>
                  {module.description ? <p>{module.description}</p> : null}
                </div>
              </div>
              <ul className="lesson-list">
                {module.lessons.map((lesson) => (
                  <li key={lesson.id}>
                    <Link
                      className="lesson-link"
                      href={`/courses/${course.slug}/lessons/${lesson.slug}`}
                    >
                      <span>{lesson.title}</span>
                      <span>{formatDuration(lesson.duration_seconds)}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
