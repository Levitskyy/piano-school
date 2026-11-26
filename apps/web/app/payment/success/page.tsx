import type { Metadata } from "next";
import Link from "next/link";

import { ClientRedirect } from "@/components/client-redirect";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { fetchWithSession, getCurrentUser } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Результат оплаты",
};

type PaymentSuccessPageProps = {
  searchParams: Promise<{ order_id?: string; order_num?: string }>;
};

export default async function PaymentSuccessPage({ searchParams }: PaymentSuccessPageProps) {
  const { order_id: orderId, order_num: orderNum } = await searchParams;
  const user = await getCurrentUser();
  if (!user) return <ClientRedirect to="/login?next=/individual-lessons" />;

  let status: string | null = null;
  const orderRef = orderNum ?? orderId;
  if (orderRef) {
    try {
      const response = await fetchWithSession(`/payments/${encodeURIComponent(orderRef)}`);
      if (response.ok) {
        status = ((await response.json()) as { status: string }).status;
      }
    } catch {
      status = null;
    }
  }

  const succeeded = status === "succeeded";

  return (
    <div className="site">
      <SiteHeader />

      <main className="section form-wide">
        <p className="eyebrow">Оплата</p>
        <h1 id="main-heading" tabIndex={-1}>
          {succeeded ? "Оплата прошла" : "Проверяем платёж"}
        </h1>
        <p className="section-lead">
          {succeeded
            ? "Занятие закреплено за вами. Ссылку на встречу преподаватель добавит в кабинете."
            : status === "pending"
              ? "Платёж ещё не подтверждён. Обновите страницу через минуту: запись появится автоматически после подтверждения оплаты."
              : "Не удалось проверить статус заказа. Если платёж был списан, напишите преподавателю — запись будет восстановлена вручную."}
        </p>

        <p className="actions">
          <Link className="button" href="/account/individual-lessons">
            Мои занятия
          </Link>
          <Link className="button button-ghost" href="/individual-lessons">
            Другие даты
          </Link>
        </p>
      </main>

      <SiteFooter />
    </div>
  );
}
