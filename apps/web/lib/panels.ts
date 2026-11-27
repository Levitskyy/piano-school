import type { UserRole } from "@/lib/auth";

export type PanelKey = "account" | "teacher" | "admin";

export type PanelLink = {
  key: PanelKey;
  href: string;
  label: string;
};

// Права проверяются и на сервере: здесь только то, что роли реально могут открыть.
const panels: readonly (PanelLink & { roles: readonly UserRole[] })[] = [
  {
    key: "account",
    href: "/account",
    label: "Кабинет ученика",
    roles: ["student", "teacher", "admin"],
  },
  {
    key: "teacher",
    href: "/teacher-panel",
    label: "Панель преподавателя",
    roles: ["teacher", "admin"],
  },
  {
    key: "admin",
    href: "/admin",
    label: "Админка",
    roles: ["admin"],
  },
];

export function panelsForRole(role: UserRole): PanelLink[] {
  return panels
    .filter((panel) => panel.roles.includes(role))
    .map(({ key, href, label }) => ({ key, href, label }));
}

export function defaultPanelHref(role: UserRole | undefined): string {
  if (!role) return "/login";
  if (role === "admin") return "/admin";
  if (role === "teacher") return "/teacher-panel";
  return "/account";
}
