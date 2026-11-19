import { redirect } from "next/navigation";

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
  if (!user) redirect("/login?next=/teacher-panel");
  if (user.role === "student") redirect("/account");

  return (
    <PanelShell user={user} nav={teacherNav}>
      {children}
    </PanelShell>
  );
}
