import type { Metadata } from "next";
import Link from "next/link";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "Контакты",
  description: "Контактные данные для связи по вопросам занятий, оплаты и обработки персональных данных Levickaya Piano.",
};

export default function ContactsPage() {
  return (
    <div className="site">
      <SiteHeader />
      <main className="legal legal-document">
        <p className="eyebrow">Контакты</p>
        <h1 id="main-heading" tabIndex={-1}>
          Контакты
        </h1>
        <p className="lead">
          По вопросам занятий, оплаты, доступа к материалам и обработки персональных данных
          напишите нам на email. Другие каналы связи не используются.
        </p>

        <section aria-labelledby="contacts-main">
          <h2 id="contacts-main">Как связаться</h2>
          <ul>
            <li>
              Email для поддержки и вопросов по персональным данным:{" "}
              <strong>levickaya.school@mail.ru</strong>
            </li>
          </ul>
          <p className="muted">Срок ответа: в течение 3 рабочих дней.</p>
        </section>

        <section aria-labelledby="contacts-requisites">
          <h2 id="contacts-requisites">Реквизиты</h2>
          <p>
            Исполнитель: Левицкая Лариса Валентиновна, плательщик налога на профессиональный
            доход (НПД), ИНН 100100548837. Почтовый адрес не публикуется.
          </p>
          <p>
            Подробные условия оказания услуг указаны в{" "}
            <Link href="/oferta">Публичной оферте</Link>.
          </p>
        </section>

        <p className="legal-links">
          См. также: <Link href="/privacy">Политику конфиденциальности</Link>.
        </p>
        <Link className="back-link" href="/">
          ← На главную
        </Link>
      </main>
      <SiteFooter />
    </div>
  );
}
