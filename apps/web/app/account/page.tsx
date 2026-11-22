import Link from "next/link";
import { ClientRedirect } from "@/components/client-redirect";
import { getCurrentUser } from "@/lib/auth";

const cards = [
  {
    href: "/individual-lessons",
    title: "Записаться на занятие",
    text: "Выбрать слот, оплатить урок или списать занятие из пакета.",
  },
  {
    href: "/account/individual-lessons",
    title: "Мои занятия",
    text: "Купленные пакеты и остаток уроков.",
  },
  {
    href: "/account/profile",
    title: "Профиль",
    text: "Имя, email и часовой пояс.",
  },
];

export default async function AccountPage() {
  const user = await getCurrentUser();
  if (!user) return <ClientRedirect to="/login?next=/account" />;

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Личный кабинет</p>
        <h1>Здравствуйте, {user.name}</h1>
        <p className="panel-lead">
          Здесь собраны ваши занятия: выбрать время, оплатить урок и посмотреть остаток
          пакета можно без помощи преподавателя.
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
