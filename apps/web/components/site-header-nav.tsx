"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { navigation, site } from "@/content/landing";
import type { User } from "@/lib/auth";

const POPOVER_OPEN_SELECTOR = ":is(:popover-open, .\\:popover-open)";

type SiteHeaderNavProps = {
  user: User | null;
};

export function SiteHeaderNav({ user }: SiteHeaderNavProps) {
  const innerRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLUListElement>(null);
  const lastWidthRef = useRef(0);
  const [isWide, setIsWide] = useState(false);

  const accountHref = !user
    ? "/login"
    : user.role === "teacher" || user.role === "admin"
      ? "/teacher-panel"
      : "/account";

  const measure = useCallback(() => {
    const inner = innerRef.current;
    const menu = menuRef.current;
    if (!inner || !menu) return;

    const wasOpen = menu.matches(POPOVER_OPEN_SELECTOR);
    const previousWide = inner.classList.contains("is-wide");

    inner.classList.add("is-measuring", "is-wide");
    menu.removeAttribute("popover");

    const fits = inner.scrollWidth <= inner.clientWidth;

    if (!fits) {
      inner.classList.remove("is-wide");
      menu.setAttribute("popover", "auto");
      if (wasOpen && !previousWide) menu.showPopover?.();
    }

    inner.classList.remove("is-measuring");
    setIsWide(fits);
  }, []);

  useEffect(() => {
    measure();

    const inner = innerRef.current;
    const menu = menuRef.current;
    if (!inner || !menu) return;

    lastWidthRef.current = inner.clientWidth;

    const observer = new ResizeObserver(() => {
      const width = inner.clientWidth;
      if (inner.classList.contains("is-wide") || width > lastWidthRef.current) {
        measure();
      }
      lastWidthRef.current = width;
    });
    observer.observe(inner);
    observer.observe(menu);

    void document.fonts?.ready.then(measure);

    return () => observer.disconnect();
  }, [measure]);

  const popoverAttr = isWide ? {} : ({ popover: "auto" } as Record<string, string>);

  return (
    <div className="header-inner" ref={innerRef}>
      <Link className="wordmark" href="/">
        <span className="wordmark-mark" aria-hidden="true">
          PS
        </span>
        <span className="wordmark-text">{site.name}</span>
      </Link>

      <nav className="site-nav" aria-label="Основная">
        <button
          className="menu-button"
          type="button"
          popoverTarget="site-menu"
          aria-controls="site-menu"
        >
          Меню
        </button>

        <ul className="mobile-menu" id="site-menu" ref={menuRef} {...popoverAttr}>
          {navigation.map((item) => (
            <li key={item.href}>
              <Link href={item.href}>{item.label}</Link>
            </li>
          ))}
          <li>
            <Link href={accountHref}>{user ? "Кабинет" : "Войти"}</Link>
          </li>
          <li className="menu-cta-item">
            <Link className="button button-small header-cta" href="/individual-lessons">
              Записаться
            </Link>
          </li>
        </ul>
      </nav>
    </div>
  );
}
