import Link from "next/link";

import { getCurrentUser } from "@/lib/auth";
import { navigation, site } from "@/content/landing";

export async function SiteHeader() {
  const user = await getCurrentUser();

  return (
    <header className="site-header">
      <a className="skip-link" href="#main-heading">
        Перейти к содержанию
      </a>
      <div className="header-inner">
        <Link className="wordmark" href="/">
          <span className="wordmark-mark" aria-hidden="true">
            PS
          </span>
          <span className="wordmark-text">{site.name}</span>
        </Link>

        <nav className="site-nav" aria-label="Основная">
          <ul className="nav-list">
            {navigation.map((item) => (
              <li key={item.href}>
                <Link href={item.href}>{item.label}</Link>
              </li>
            ))}
            <li>
              {user ? (
                <Link href="/account">Кабинет</Link>
              ) : (
                <Link href="/login">Войти</Link>
              )}
            </li>
          </ul>

          <button
            className="menu-button"
            type="button"
            popoverTarget="mobile-menu"
            aria-controls="mobile-menu"
          >
            Меню
          </button>

          <ul className="mobile-menu" id="mobile-menu" popover="auto">
            {navigation.map((item) => (
              <li key={item.href}>
                <Link href={item.href}>{item.label}</Link>
              </li>
            ))}
            <li>
              {user ? (
                <Link href="/account">Кабинет</Link>
              ) : (
                <Link href="/login">Войти</Link>
              )}
            </li>
            <li>
              <Link className="button" href="/#formats">
                Записаться
              </Link>
            </li>
          </ul>
        </nav>

        <Link className="button button-small header-cta" href="/#formats">
          Записаться
        </Link>
      </div>
    </header>
  );
}
