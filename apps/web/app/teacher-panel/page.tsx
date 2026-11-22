import Link from "next/link";

const cards = [
  {
    href: "/teacher-panel/lessons",
    title: "Занятия",
    text: "Записи учеников, расписание и ссылки на встречи.",
  },
  {
    href: "/teacher-panel/students",
    title: "Ученики",
    text: "Активные ученики и остатки занятий в пакетах.",
  },
];

export default function TeacherPanelPage() {
  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Преподаватель</p>
        <h1>Рабочий стол</h1>
        <p className="panel-lead">
          Здесь собраны записи на индивидуальные уроки и данные учеников. Расписание уже
          подключено к API; остальные разделы наполняются по этапам.
        </p>
      </header>

      <div className="panel-grid">
        {cards.map((card) => (
          <Link className="panel-card" href={card.href} key={card.href}>
            <h2>{card.title}</h2>
            <p>{card.text}</p>
            <span aria-hidden="true">→</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
