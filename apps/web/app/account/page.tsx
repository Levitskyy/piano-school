import Link from "next/link";
import { redirect } from "next/navigation";

import { EmptyState } from "@/components/empty-state";
import { getCurrentUser } from "@/lib/auth";

const cards = [
  {
    href: "/account/courses",
    title: "Мои курсы",
    text: "Курс, модули, уроки, материалы, домашние задания и сопровождение.",
  },
  {
    href: "/account/individual-lessons",
    title: "Индивидуальные занятия",
    text: "Разовые уроки и остаток занятий в пакете.",
  },
  {
    href: "/account/orders",
    title: "Заказы",
    text: "Покупки, статус оплаты и доступы.",
  },
  {
    href: "/account/profile",
    title: "Профиль",
    text: "Имя, email, часовой пояс и язык интерфейса.",
  },
];

export default async function AccountPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/account");

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Личный кабинет</p>
        <h1>Здравствуйте, {user.name}</h1>
        <p className="panel-lead">
          Здесь будут курсы, занятия и обратная связь. Пока аккаунт новый, разделы
          выглядят пустыми — это нормально.
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

      <section className="panel-section" aria-labelledby="next-steps">
        <div className="panel-section-head">
          <h2 id="next-steps">С чего начать</h2>
        </div>
        <EmptyState
          title="Пока нет активного обучения"
          text="Выберите семестр или формат занятий на сайте. После подтверждения оплаты доступ появится в кабинете автоматически."
          action={
            <Link className="button" href="/#formats">
              Посмотреть форматы
            </Link>
          }
        />
      </section>
    </div>
  );
}
