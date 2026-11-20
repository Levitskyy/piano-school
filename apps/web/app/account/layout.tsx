import { ClientRedirect } from "@/components/client-redirect";
import { PanelShell } from "@/components/panel-shell";
import { getCurrentUser } from "@/lib/auth";

const accountNav = [
  { href: "/account", label: "Обзор" },
  { href: "/account/courses", label: "Мои курсы" },
  { href: "/account/individual-lessons", label: "Индивидуальные занятия" },
  { href: "/account/orders", label: "Заказы" },
  { href: "/account/profile", label: "Профиль" },
];

export default async function AccountLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const user = await getCurrentUser();
  if (!user) return <ClientRedirect to="/login?next=/account" />;

  return (
    <PanelShell user={user} nav={accountNav}>
      {children}
    </PanelShell>
  );
}
