import { ClientRedirect } from "@/components/client-redirect";
import { PanelShell } from "@/components/panel-shell";
import { getCurrentUser } from "@/lib/auth";

const teacherNav = [
  { href: "/teacher-panel", label: "Обзор" },
  { href: "/teacher-panel/submissions", label: "Домашние задания" },
  { href: "/teacher-panel/students", label: "Ученики" },
  { href: "/teacher-panel/lessons", label: "Занятия" },
];

export default async function TeacherPanelLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const user = await getCurrentUser();
  if (!user) return <ClientRedirect to="/login?next=/teacher-panel" />;
  if (user.role === "student") return <ClientRedirect to="/account" />;

  return (
    <PanelShell user={user} nav={teacherNav}>
      {children}
    </PanelShell>
  );
}
