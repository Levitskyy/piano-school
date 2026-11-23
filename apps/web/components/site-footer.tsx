import Link from "next/link";

import { navigation, site } from "@/content/landing";

const legalLinks = [
  { label: "Публичная оферта", href: "/oferta" },
  { label: "Политика конфиденциальности", href: "/privacy" },
  { label: "Контакты", href: "/contacts" },
];

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <p className="footer-wordmark">{site.name}</p>
          <p className="footer-tagline">{site.tagline}</p>
        </div>

        <nav aria-label="Дополнительная">
          <p className="footer-heading">Разделы</p>
          <ul className="footer-links">
            {navigation.map((item) => (
              <li key={item.href}>
                <Link href={item.href}>{item.label}</Link>
              </li>
            ))}
          </ul>
        </nav>

        <nav aria-label="Документы">
          <p className="footer-heading">Документы</p>
          <ul className="footer-links">
            {legalLinks.map((item) => (
              <li key={item.href}>
                <Link href={item.href}>{item.label}</Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>

      <p className="footer-note">© 2026 {site.name}. Индивидуальные занятия онлайн.</p>
    </footer>
  );
}