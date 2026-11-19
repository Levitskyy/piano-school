import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { EmptyState } from "@/components/empty-state";
import { LessonProgress } from "@/components/lesson-progress";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { fetchWithSession } from "@/lib/auth";
import type { LessonDetail } from "@/lib/catalog";

type LessonPageProps = {
  params: Promise<{ slug: string; lessonSlug: string }>;
};

export const metadata: Metadata = {
  title: "Урок",
};

export default async function LessonPage({ params }: LessonPageProps) {
  const { slug, lessonSlug } = await params;
  const nextPath = `/courses/${slug}/lessons/${lessonSlug}`;

  let response: Response;
  try {
    response = await fetchWithSession(
      `/courses/${encodeURIComponent(slug)}/lessons/${encodeURIComponent(lessonSlug)}`,
    );
  } catch {
    return (
      <div className="site">
        <SiteHeader />
        <main className="section">
          <EmptyState
            title="Сервис временно недоступен"
            text="Не удалось загрузить урок. Попробуйте обновить страницу через минуту."
          />
        </main>
        <SiteFooter />
      </div>
    );
  }

  if (response.status === 401) {
    redirect(`/login?next=${encodeURIComponent(nextPath)}`);
  }

  if (response.status === 403) {
    return (
      <div className="site">
        <SiteHeader />
        <main className="section">
          <EmptyState
            title="Нужен доступ к курсу"
            text="Этот урок доступен после покупки курса. Вернитесь к программе и выберите подходящий вариант."
            action={
              <Link className="button" href={`/courses/${slug}`}>
                Вернуться к курсу
              </Link>
            }
          />
        </main>
        <SiteFooter />
      </div>
    );
  }

  if (response.status === 404) notFound();

  if (!response.ok) {
    return (
      <div className="site">
        <SiteHeader />
        <main className="section">
          <EmptyState
            title="Не удалось открыть урок"
            text="Попробуйте обновить страницу. Если ошибка повторяется, вернитесь в кабинет."
            action={
              <Link className="button" href="/account/courses">
                В мои курсы
              </Link>
            }
          />
        </main>
        <SiteFooter />
      </div>
    );
  }

  const lesson = (await response.json()) as LessonDetail;

  return (
    <div className="site">
      <SiteHeader />

      <main>
        <section className="section lesson-page">
          <Link
            className="back-link"
            href={`/account/courses/${lesson.course_slug}`}
          >
            ← {lesson.course_title}
          </Link>
          <p className="eyebrow">{lesson.module_title}</p>
          <h1 id="main-heading" tabIndex={-1}>
            {lesson.title}
          </h1>
          <p className="body-text">{lesson.description}</p>

          <div className="video-placeholder">
            <span className="video-mark" aria-hidden="true">
              ▶
            </span>
            <div>
              <h2>Видео урока</h2>
              <p>
                HLS-плеер появится после подключения хранилища. Сейчас урок открыт,
                чтобы проверить доступ и прогресс.
              </p>
            </div>
          </div>

          <div className="lesson-layout">
            <section aria-labelledby="materials-title">
              <div className="panel-section-head">
                <h2 id="materials-title">Материалы</h2>
              </div>
              {lesson.materials.length === 0 ? (
                <p className="body-text">Ноты и файлы появятся позже.</p>
              ) : (
                <ul className="material-list">
                  {lesson.materials.map((material) => (
                    <li key={material.id}>
                      <span>{material.title}</span>
                      {material.url ? (
                        <a href={material.url} target="_blank" rel="noreferrer">
                          Открыть
                        </a>
                      ) : (
                        <span className="muted">Готовится</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <LessonProgress
              courseSlug={lesson.course_slug}
              lessonSlug={lesson.slug}
              initialStatus={lesson.progress?.status ?? "not_started"}
            />
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
