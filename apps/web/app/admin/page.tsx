import Link from "next/link";

const cards = [
  {
    href: "/admin/users",
    title: "Пользователи",
    text: "Аккаунты, роли и доступы.",
  },
  {
    href: "/admin/products",
    title: "Цены",
    text: "Стоимость разового урока и пакетов занятий.",
  },
  {
    href: "/admin/promo-codes",
    title: "Промокоды",
    text: "Создавать одноразовые процентные скидки на покупку.",
  },
  {
    href: "/admin/orders",
    title: "Заказы",
    text: "Платежи и статусы записи на урок.",
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
            <span aria-hidden="true">→</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
