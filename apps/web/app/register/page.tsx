import type { Metadata } from "next";
import { ClientRedirect } from "@/components/client-redirect";
import { AuthForm } from "@/components/auth-form";
import { AuthShell } from "@/components/auth-shell";
import { getCurrentUser } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Регистрация",
  description: "Создайте аккаунт ученика Piano School.",
};

export default async function RegisterPage() {
  const user = await getCurrentUser();
  if (user) return <ClientRedirect to="/account" />;

  return (
    <AuthShell
      eyebrow="Новый аккаунт"
      title="Регистрация"
      lead="Создайте аккаунт, чтобы получить доступ к курсам и записи на уроки."
      aside={
        <p className="auth-note">
          После регистрации вы попадёте в личный кабинет. Курсы и занятия появятся там
          после покупки.
        </p>
      }
    >
      <AuthForm mode="register" headingId="main-heading" />
    </AuthShell>
  );
}
