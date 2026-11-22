import type { Metadata } from "next";
import { ClientRedirect } from "@/components/client-redirect";
import { AuthForm } from "@/components/auth-form";
import { AuthShell } from "@/components/auth-shell";
import { getCurrentUser } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Вход",
  description: "Вход в личный кабинет Piano School.",
};

type LoginPageProps = {
  searchParams: Promise<{ next?: string | string[] }>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const user = await getCurrentUser();
  if (user) return <ClientRedirect to="/account" />;

  const params = await searchParams;
  const next = typeof params.next === "string" ? params.next : undefined;

  return (
    <AuthShell
      eyebrow="Личный кабинет"
      title="Вход"
      lead="Расписание занятий, купленные пакеты и статус оплаты — в одном месте."
    >
      <AuthForm mode="login" headingId="main-heading" next={next} />
    </AuthShell>
  );
}
