import type { Metadata } from "next";
import Link from "next/link";

import { AuthShell } from "@/components/auth-shell";
import { ResetPasswordForm } from "@/components/reset-password-form";

export const metadata: Metadata = {
  title: "Новый пароль",
  description: "Сброс пароля в аккаунте Piano School.",
};

type ResetPasswordPageProps = {
  searchParams: Promise<{ token?: string | string[] }>;
};

export default async function ResetPasswordPage({
  searchParams,
}: ResetPasswordPageProps) {
  const params = await searchParams;
  const token = typeof params.token === "string" ? params.token : "";

  return (
    <AuthShell
      eyebrow="Доступ к аккаунту"
      title="Новый пароль"
      lead="Придумайте новый пароль. После сохранения все старые сеансы будут завершены."
    >
      {token ? (
        <ResetPasswordForm token={token} />
      ) : (
        <div className="form-notice" role="alert">
          <p>Ссылка неполная или устарела.</p>
          <p>
            <Link href="/forgot-password">Запросить новую ссылку</Link>
          </p>
        </div>
      )}
    </AuthShell>
  );
}
