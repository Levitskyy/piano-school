"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export type PanelNavItem = {
  href: string;
  label: string;
};

export function PanelNav({ items }: { items: PanelNavItem[] }) {
  const pathname = usePathname();

  return (
    <nav className="panel-nav" aria-label="Разделы кабинета">
      <ul>
        {items.map((item) => {
          const active =
            pathname === item.href ||
            (item.href !== "/account" &&
              item.href !== "/teacher-panel" &&
              item.href !== "/admin" &&
              pathname.startsWith(`${item.href}/`));

          return (
            <li key={item.href}>
              <Link href={item.href} aria-current={active ? "page" : undefined}>
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
