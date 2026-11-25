import type { Metadata } from "next";

import { AuthShell } from "@/components/auth-shell";
import { VerifyEmailForm } from "@/components/verify-email-form";
import { getCurrentUser } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Подтверждение email",
  description: "Подтвердите email в аккаунте Levickaya Piano.",
};

type VerifyEmailPageProps = {
  searchParams: Promise<{
    token?: string | string[];
    sent?: string | string[];
    failed?: string | string[];
    verified?: string | string[];
  }>;
};

export default async function VerifyEmailPage({
  searchParams,
}: VerifyEmailPageProps) {
  const params = await searchParams;
  const token = typeof params.token === "string" ? params.token : "";
  const sent = params.sent === "1";
  const failed = params.failed === "1";
  const confirmed = params.verified === "1";
  const currentUser = await getCurrentUser();
  const verified = confirmed || Boolean(currentUser?.email_verified_at);

  return (
    <AuthShell
      eyebrow="Подтверждение аккаунта"
      title={verified ? "Email подтверждён" : "Проверьте почту"}
      lead={
        verified
          ? "Готово: теперь можно оплачивать занятия и записываться на урок."
          : failed
            ? "Отправка письма не удалась. Попробуйте ещё раз — это не отменило регистрацию."
            : "Откройте письмо от Levickaya Piano и перейдите по ссылке. Она действует 24 часа."
      }
    >
      <VerifyEmailForm
        token={token}
        sent={sent}
        failed={failed}
        verified={verified}
      />
    </AuthShell>
  );
}
