import type { Metadata } from "next";
import Link from "next/link";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "Политика конфиденциальности",
  description: "Правила обработки персональных данных в Piano School.",
};

export default function PrivacyPage() {
  return (
    <div className="site">
      <SiteHeader />
      <main className="legal">
        <p className="eyebrow">Документы</p>
        <h1 id="main-heading" tabIndex={-1}>
          Политика конфиденциальности
        </h1>
        <p className="lead">
          Документ готовится к запуску. Здесь появятся правила обработки персональных данных,
          включая данные детей.
        </p>
        <Link className="back-link" href="/">
          ← На главную
        </Link>
      </main>
      <SiteFooter />
    </div>
  );
}
