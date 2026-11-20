import { ClientRedirect } from "@/components/client-redirect";
import { PanelShell } from "@/components/panel-shell";
import { getCurrentUser } from "@/lib/auth";

const adminNav = [
  { href: "/admin", label: "Обзор" },
  { href: "/admin/users", label: "Пользователи" },
  { href: "/admin/courses", label: "Курсы" },
  { href: "/admin/products", label: "Продукты" },
  { href: "/admin/orders", label: "Заказы" },
  { href: "/admin/settings", label: "Настройки" },
];

export default async function AdminLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const user = await getCurrentUser();
  if (!user) return <ClientRedirect to="/login?next=/admin" />;
  if (user.role !== "admin") {
    return (
      <ClientRedirect
        to={user.role === "teacher" ? "/teacher-panel" : "/account"}
      />
    );
  }

  return (
    <PanelShell user={user} nav={adminNav}>
      {children}
    </PanelShell>
  );
}
