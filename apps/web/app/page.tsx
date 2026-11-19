import Link from "next/link";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { about, cta, faq, formats, hero, manifesto, process, program } from "@/content/landing";

function number(index: number) {
  return String(index + 1).padStart(2, "0");
}

export default function HomePage() {
  return (
    <div className="site">
      <SiteHeader />

      <main>
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow">{hero.eyebrow}</p>
            <h1 id="main-heading" tabIndex={-1}>
              {hero.title}
            </h1>
            <p className="lead">{hero.lead}</p>

            <div className="actions">
              <Link className="button" href={hero.primaryCta.href}>
                {hero.primaryCta.label}
              </Link>
              <Link className="button button-ghost" href={hero.secondaryCta.href}>
                {hero.secondaryCta.label}
              </Link>
            </div>

            <ul className="hero-meta" aria-label="Кратко о занятиях">
              {hero.meta.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="hero-visual">
            <div className="score-card">
              <div className="score-card-head">
                <span className="score-kicker">Урок 01</span>
                <span>Посадка и звук</span>
              </div>

              <svg
                className="score-staff"
                viewBox="0 0 440 260"
                aria-hidden="true"
                focusable="false"
              >
                {[70, 100, 130, 160, 190].map((y) => (
                  <line key={y} x1="20" x2="420" y1={y} y2={y} />
                ))}

                <ellipse cx="110" cy="160" rx="11" ry="8" transform="rotate(-18 110 160)" />
                <rect x="118" y="102" width="3.5" height="58" />

                <ellipse cx="165" cy="130" rx="11" ry="8" transform="rotate(-18 165 130)" />
                <rect x="173" y="72" width="3.5" height="58" />

                <ellipse cx="230" cy="145" rx="11" ry="8" transform="rotate(-18 230 145)" />
                <rect x="238" y="87" width="3.5" height="58" />

                <ellipse
                  className="score-note-accent"
                  cx="320"
                  cy="115"
                  rx="11"
                  ry="8"
                  transform="rotate(-18 320 115)"
                />
                <rect
                  className="score-note-accent"
                  x="328"
                  y="57"
                  width="3.5"
                  height="58"
                />
              </svg>

              <div className="score-card-foot">
                <span>видео · ноты · практика</span>
                <span className="score-index">01 / 12</span>
              </div>
            </div>
          </div>
        </section>

        <section className="section" id="formats">
          <div className="section-head">
            <p className="eyebrow">Форматы</p>
            <h2>Три способа учиться</h2>
          </div>

          <ul className="format-grid" role="list">
            {formats.map((format, index) => (
              <li className="format-card" key={format.title}>
                <span className="card-number">{number(index)}</span>
                <h3>{format.title}</h3>
                <p>{format.description}</p>
                <span className="card-meta">{format.meta}</span>
              </li>
            ))}
          </ul>

          <p className="section-more">
            <Link href="/courses">Курс и варианты покупки →</Link>
          </p>
        </section>

        <section className="section split" id="about">
          <figure className="portrait">
            <div className="portrait-frame" aria-hidden="true">
              <span>PS</span>
            </div>
            <figcaption>{about.portraitCaption}</figcaption>
          </figure>

          <div>
            <p className="eyebrow">{about.eyebrow}</p>
            <h2>{about.title}</h2>
            {about.paragraphs.map((paragraph) => (
              <p className="body-text" key={paragraph}>
                {paragraph}
              </p>
            ))}
            <ul className="feature-list">
              {about.points.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </div>
        </section>

        <section className="section" id="program">
          <div className="section-head">
            <p className="eyebrow">{program.eyebrow}</p>
            <h2>{program.title}</h2>
            <p className="section-lead">{program.lead}</p>
          </div>

          <ol className="module-list">
            {program.modules.map((module, index) => (
              <li key={module.title}>
                <span className="module-number">{number(index)}</span>
                <div>
                  <h3>{module.title}</h3>
                  <p>{module.description}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className="section" id="process">
          <div className="section-head">
            <p className="eyebrow">{process.eyebrow}</p>
            <h2>{process.title}</h2>
          </div>

          <ol className="step-grid">
            {process.steps.map((step, index) => (
              <li key={step.title}>
                <span className="step-number">{number(index)}</span>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </li>
            ))}
          </ol>
        </section>

        <div className="manifesto">
          <blockquote>
            <p>«{manifesto.quote}»</p>
            <p className="manifesto-author">— {manifesto.attribution}</p>
          </blockquote>
        </div>

        <section className="section" id="faq" aria-labelledby="faq-title">
          <div className="section-head">
            <p className="eyebrow">Вопросы</p>
            <h2 id="faq-title">Коротко о главном</h2>
          </div>

          <div className="accordion">
            {faq.map((item) => (
              <details key={item.question}>
                <summary>{item.question}</summary>
                <p>{item.answer}</p>
              </details>
            ))}
          </div>
        </section>

        <section className="cta-band">
          <p className="eyebrow">{cta.eyebrow}</p>
          <h2>{cta.title}</h2>
          <p className="section-lead">{cta.text}</p>
          <Link className="button" href={cta.button.href}>
            {cta.button.label}
          </Link>
          <p className="cta-note">{cta.note}</p>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
