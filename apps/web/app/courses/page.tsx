import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { EmptyState } from "@/components/empty-state";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { getPublicCourses, levelLabel } from "@/lib/catalog";
import { coursesEnabled } from "@/lib/feature-flags";

export const metadata: Metadata = {
  title: "Курсы",
  description: "Курс фортепиано: самостоятельное обучение или сопровождение преподавателя.",
};

export default async function CoursesPage() {
  if (!coursesEnabled) notFound();
  const courses = await getPublicCourses();

  return (
    <div className="site">
      <SiteHeader />

      <main>
        <section className="section">
          <div className="section-head">
            <p className="eyebrow">Каталог</p>
            <h1 id="main-heading" tabIndex={-1}>
              Один курс, два формата
            </h1>
            <p className="section-lead">
              Можно заниматься самостоятельно или добавить сопровождение преподавателя.
              Программа одна — различаются обратная связь и поддержка.
            </p>
          </div>

          {courses.length === 0 ? (
            <EmptyState
              title="Курс готовится"
              text="Программа и цены ещё не опубликованы. Загляните позже или напишите преподавателю."
              action={
                <Link className="button button-ghost" href="/#formats">
                  Посмотреть форматы
                </Link>
              }
            />
          ) : (
            <div className="course-grid">
              {courses.map((course) => (
                <Link className="course-card" href={`/courses/${course.slug}`} key={course.id}>
                  <div className="course-card-top">
                    <p className="card-meta">{levelLabel(course.level)}</p>
                    <span className="course-card-mark" aria-hidden="true">
                      LP
                    </span>
                  </div>
                  <h2>{course.title}</h2>
                  {course.subtitle ? <p className="course-card-subtitle">{course.subtitle}</p> : null}
                  <p>{course.description}</p>
                  <div className="course-card-foot">
                    <span>{course.offers.length} варианта покупки</span>
                    <span>Открыть →</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
