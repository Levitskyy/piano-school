import Link from "next/link";

import { EmptyState } from "@/components/empty-state";

const cards = [
  {
    href: "/admin/users",
    title: "Пользователи",
    text: "Аккаунты, роли и доступы.",
  },
  {
    href: "/admin/courses",
    title: "Курсы",
    text: "Семестры, модули, уроки и материалы.",
  },
  {
    href: "/admin/products",
    title: "Продукты",
    text: "Цены, пакеты занятий и сопровождение.",
  },
  {
    href: "/admin/orders",
    title: "Заказы",
    text: "Платежи, доступы и возвраты.",
  },
];

export default function AdminPage() {
  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Администратор</p>
        <h1>Управление школой</h1>
        <p className="panel-lead">
          Каркас административной панели. Список пользователей уже подключён к API,
          остальные разделы будут наполняться по этапам.
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

      <section className="panel-section" aria-labelledby="admin-next">
        <div className="panel-section-head">
          <h2 id="admin-next">Что уже работает</h2>
        </div>
        <EmptyState
          title="Роли и доступ проверяются на сервере"
          text="Студент не попадёт в админку, преподаватель — в раздел администратора. API дополнительно проверяет роль при каждом запросе."
          action={
            <Link className="button" href="/admin/users">
              Открыть пользователей
            </Link>
          }
        />
      </section>
    </div>
  );
}
