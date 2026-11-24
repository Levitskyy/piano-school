import Link from "next/link";

import { LogoutButton } from "@/components/logout-button";
import { PanelNav, type PanelNavItem } from "@/components/panel-nav";
import type { User } from "@/lib/auth";

const roleLabels: Record<User["role"], string> = {
  student: "Ученик",
  teacher: "Преподаватель",
  admin: "Администратор",
};

type PanelShellProps = {
  user: User;
  nav: PanelNavItem[];
  children: React.ReactNode;
};

export function PanelShell({ user, nav, children }: PanelShellProps) {
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

        <PanelNav items={nav} />
      </header>

      <main className="panel-main">{children}</main>
    </div>
  );
}
