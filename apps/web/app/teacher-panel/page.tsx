import Link from "next/link";

import { EmptyState } from "@/components/empty-state";

const cards = [
  {
    href: "/teacher-panel/submissions",
    title: "Домашние задания",
    text: "Записи учеников, комментарии и статусы проверки.",
  },
  {
    href: "/teacher-panel/students",
    title: "Ученики",
    text: "Активные ученики, доступы и остатки занятий.",
  },
  {
    href: "/teacher-panel/lessons",
    title: "Занятия",
    text: "Запросы на индивидуальные уроки и ссылки на встречи.",
  },
];

export default function TeacherPanelPage() {
  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Преподаватель</p>
        <h1>Рабочий стол</h1>
        <p className="panel-lead">
          Здесь появятся работы на проверку, расписание и ученики. Пока это каркас
          панели с проверенной защитой по роли.
        </p>
      </header>

      <div className="panel-grid">
        {cards.map((card) => (
          <Link className="panel-card" href={card.href} key={card.href}>
            <h2>{card.title}</h2>
            <p>{card.text}</p>
            <span className="panel-card-link">Открыть →</span>
          </Link>
        ))}
      </div>

      <section className="panel-section" aria-labelledby="teacher-next">
        <div className="panel-section-head">
          <h2 id="teacher-next">Ближайший шаг</h2>
        </div>
        <EmptyState
          title="Проверка работ ещё не подключена"
          text="На следующем этапе сюда попадут загруженные файлы учеников с текстовыми комментариями и статусами проверки."
        />
      </section>
    </div>
  );
}
