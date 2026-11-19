import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { EmptyState } from "@/components/empty-state";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { getCurrentUser } from "@/lib/auth";
import {
  formatDuration,
  formatPrice,
  getAccountCourses,
  getPublicCourse,
  levelLabel,
} from "@/lib/catalog";

type CoursePageProps = {
  params: Promise<{ slug: string }>;
};

export async function generateMetadata({ params }: CoursePageProps): Promise<Metadata> {
  const { slug } = await params;
  const course = await getPublicCourse(slug);
  if (!course) return { title: "Курс не найден" };
  return {
    title: course.title,
    description: course.subtitle ?? course.description,
  };
}

export default async function CoursePage({ params }: CoursePageProps) {
  const { slug } = await params;
  const course = await getPublicCourse(slug);
  if (!course) notFound();

  const user = await getCurrentUser();
  const accountCourses = user ? await getAccountCourses() : [];
  const access = accountCourses.find((item) => item.course.slug === course.slug);

  const offers = course.offers.filter((offer) => offer.is_active);

  return (
    <div className="site">
      <SiteHeader />

      <main>
        <section className="section course-hero">
          <Link className="back-link" href="/courses">
            ← Все курсы
          </Link>
          <p className="eyebrow">{levelLabel(course.level)}</p>
          <h1 id="main-heading" tabIndex={-1}>
            {course.title}
          </h1>
          {course.subtitle ? <p className="lead">{course.subtitle}</p> : null}
          <p className="body-text course-description">{course.description}</p>

          <div className="course-facts">
            <span>{course.modules.length} модулей</span>
            <span>
              {course.modules.reduce((total, module) => total + module.lessons.length, 0)}{" "}
              уроков
            </span>
            <span>Онлайн · в своём темпе</span>
          </div>

          {access ? (
            <div className="access-note" role="status">
              <p>У вас уже есть доступ к этому курсу.</p>
              <Link className="button" href={`/account/courses/${course.slug}`}>
                Открыть в кабинете
              </Link>
            </div>
          ) : null}
        </section>

        {!access ? (
          <section className="section" aria-labelledby="offers-title">
            <div className="section-head">
              <p className="eyebrow">Варианты покупки</p>
              <h2 id="offers-title">Выберите формат</h2>
              <p className="section-lead">
                Содержание курса одинаковое. Второй вариант добавляет период
                сопровождения преподавателя — без автопродления.
              </p>
            </div>
  
            {offers.length === 0 ? (
              <EmptyState
                title="Цены уточняются"
                text="Варианты покупки появятся, когда будут утверждены стоимость и состав сопровождения."
              />
            ) : (
              <div className="offer-grid">
                {offers.map((offer) => (
                  <article className="offer-card" key={offer.id}>
                    <p className="card-meta">
                      {offer.kind === "with_mentorship" ? "С сопровождением" : "Самостоятельно"}
                    </p>
                    <h3>{offer.title}</h3>
                    <p>{offer.description}</p>
                    {offer.mentorship_days ? (
                      <p className="offer-meta">
                        {offer.mentorship_days} дней сопровождения
                      </p>
                    ) : null}
                    <p className="offer-price">{formatPrice(offer)}</p>
                    <p className="offer-note">
                      Оплата появится после подключения ЮKassa на следующем этапе.
                    </p>
                  </article>
                ))}
              </div>
            )}
          </section>

          ) : null}

        <section className="section" aria-labelledby="program-title">
          <div className="section-head">
            <p className="eyebrow">Программа</p>
            <h2 id="program-title">Что внутри</h2>
          </div>

          <ol className="course-program">
            {course.modules.map((module, index) => (
              <li key={module.id}>
                <div className="course-module-head">
                  <span className="module-number">{String(index + 1).padStart(2, "0")}</span>
                  <div>
                    <h3>{module.title}</h3>
                    <p>{module.description}</p>
                  </div>
                </div>

                <ul className="lesson-list">
                  {module.lessons.map((lesson) => (
                    <li key={lesson.id}>
                      {access ? (
                        <Link
                          className="lesson-link"
                          href={`/courses/${course.slug}/lessons/${lesson.slug}`}
                        >
                          <span>{lesson.title}</span>
                          <span>{formatDuration(lesson.duration_seconds)}</span>
                        </Link>
                      ) : (
                        <div className="lesson-link lesson-link-locked">
                          <span>{lesson.title}</span>
                          <span>После покупки</span>
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ol>
        </section>

        <section className="cta-band">
          <p className="eyebrow">Начало</p>
          <h2>{access ? "Курс уже открыт" : "Начните с одного курса"}</h2>
          <p className="section-lead">
            {access
              ? "Продолжайте с того места, где остановились. Прогресс сохраняется в кабинете."
              : "Зарегистрируйтесь, чтобы подготовить кабинет. Оплата и доступ появятся после подключения ЮKassa."}
          </p>
          <Link
            className="button"
            href={access ? `/account/courses/${course.slug}` : "/register"}
          >
            {access ? "Продолжить обучение" : "Создать аккаунт"}
          </Link>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
