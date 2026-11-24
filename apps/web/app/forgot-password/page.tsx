import type { Metadata } from "next";

import { AuthShell } from "@/components/auth-shell";
import { ForgotPasswordForm } from "@/components/forgot-password-form";

export const metadata: Metadata = {
  title: "Восстановление пароля",
  description: "Восстановление доступа к аккаунту Levickaya Piano.",
};

export default function ForgotPasswordPage() {
  return (
    <AuthShell
      eyebrow="Доступ к аккаунту"
      title="Восстановление пароля"
      lead="Укажите email, на который зарегистрирован аккаунт. Мы отправим ссылку для сброса пароля."
    >
      <ForgotPasswordForm />
    </AuthShell>
  );
}
