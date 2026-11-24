import type { Metadata } from "next";
import { ClientRedirect } from "@/components/client-redirect";
import { AuthForm } from "@/components/auth-form";
import { AuthShell } from "@/components/auth-shell";
import { getCurrentUser } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Регистрация",
  description: "Создайте аккаунт ученика Levickaya Piano.",
};

export default async function RegisterPage() {
  const user = await getCurrentUser();
  if (user) return <ClientRedirect to="/account" />;

  return (
    <AuthShell
      eyebrow="Новый аккаунт"
      title="Регистрация"
      lead="Создайте аккаунт, чтобы выбрать урок, оплатить его и увидеть запись в кабинете."
      aside={
        <p className="auth-note">
          После регистрации вы попадёте в личный кабинет. Купленные занятия появятся там
          после оплаты.
        </p>
      }
    >
      <AuthForm mode="register" headingId="main-heading" />
    </AuthShell>
  );
}
