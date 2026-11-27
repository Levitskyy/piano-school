import Link from "next/link";

import { LogoutButton } from "@/components/logout-button";
import { PanelNav, type PanelNavItem } from "@/components/panel-nav";
import type { User } from "@/lib/auth";
import { panelsForRole, type PanelKey } from "@/lib/panels";

const roleLabels: Record<User["role"], string> = {
  student: "Ученик",
  teacher: "Преподаватель",
  admin: "Администратор",
};

type PanelShellProps = {
  user: User;
  panel: PanelKey;
  nav: PanelNavItem[];
  children: React.ReactNode;
};

export function PanelShell({ user, panel, nav, children }: PanelShellProps) {
  const panels = panelsForRole(user.role);

  return (
    <div className="panel">
      <header className="panel-header">
        <div className="panel-header-inner">
          <Link className="wordmark" href="/">
            <span className="wordmark-mark" aria-hidden="true">
              LP
            </span>
            <span className="wordmark-text">Levickaya Piano</span>
          </Link>

          <div className="panel-account">
            <div className="panel-account-text">
              <span className="panel-account-name">{user.name}</span>
              <span className="panel-account-role">{roleLabels[user.role]}</span>
            </div>
            <LogoutButton />
          </div>
        </div>

        {panels.length > 1 ? (
          <div className="panel-switch-row">
            <nav className="panel-switch" aria-label="Доступные кабинеты">
              <span className="panel-switch-label">Кабинет:</span>
              <ul>
                {panels.map((item) => (
                  <li key={item.key}>
                    <Link
                      href={item.href}
                      aria-current={item.key === panel ? "page" : undefined}
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          </div>
        ) : null}

        <PanelNav items={nav} />
      </header>

      <main className="panel-main">{children}</main>
    </div>
  );
}
