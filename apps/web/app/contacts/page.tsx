import type { Metadata } from "next";
import Link from "next/link";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "Контакты",
  description: "Контактные данные для связи по вопросам занятий и сайта Levickaya Piano.",
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
          По вопросам занятий, оплаты, доступа к материалам и обработки персональных данных вы
          можете связаться с нами удобным способом.
        </p>

        <section aria-labelledby="contacts-main">
          <h2 id="contacts-main">Как связаться</h2>
          <ul>
            <li>
              Email: <strong>[УТОЧНИТЬ: email поддержки / для ПДн]</strong>
            </li>
            <li>
              Телефон: <strong>[УТОЧНИТЬ, если будет указан]</strong>
            </li>
            <li>
              Социальные сети / мессенджеры: <strong>[УТОЧНИТЬ, при необходимости]</strong>
            </li>
          </ul>
          <p className="muted">
            Ориентировочный срок ответа: <strong>[УТОЧНИТЬ, например, в течение 3 рабочих дней]</strong>.
          </p>
        </section>

        <section aria-labelledby="contacts-requisites">
          <h2 id="contacts-requisites">Реквизиты</h2>
          <p>
            Подробные реквизиты исполнителя публикуются в{" "}
            <Link href="/oferta">Публичной оферте</Link>.
          </p>
        </section>

        <p className="legal-links">
          См. также: <Link href="/privacy">Политика конфиденциальности</Link>.
        </p>
        <Link className="back-link" href="/">
          ← На главную
        </Link>
      </main>
      <SiteFooter />
    </div>
  );
}