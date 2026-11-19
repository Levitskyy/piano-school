import type { Metadata } from "next";
import Link from "next/link";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "Публичная оферта",
  description: "Условия оказания услуг и оплаты обучения в Piano School.",
};

export default function OfertaPage() {
  return (
    <div className="site">
      <SiteHeader />
      <main className="legal">
        <p className="eyebrow">Документы</p>
        <h1 id="main-heading" tabIndex={-1}>
          Публичная оферта
        </h1>
        <p className="lead">
          Документ готовится к запуску. Здесь появятся условия оказания услуг, оплаты и возврата.
        </p>
        <Link className="back-link" href="/">
          ← На главную
        </Link>
      </main>
      <SiteFooter />
    </div>
  );
}
