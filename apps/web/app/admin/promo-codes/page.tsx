import type { Metadata } from "next";

import { AdminPromoForm } from "@/components/admin-promo-form";
import { EmptyState } from "@/components/empty-state";
import { fetchWithSession } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Промокоды",
};

type PromoCode = {
  id: string;
  code: string;
  discount_percent: string | number;
  is_active: boolean;
  used_at: string | null;
  created_at: string;
};

async function loadPromoCodes(): Promise<PromoCode[] | null> {
  try {
    const response = await fetchWithSession("/admin/promo-codes");
    if (!response.ok) return null;
    return (await response.json()) as PromoCode[];
  } catch {
    return null;
  }
}

export default async function AdminPromoCodesPage() {
  const promoCodes = await loadPromoCodes();

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Администратор</p>
        <h1>Промокоды</h1>
        <p className="panel-lead">
          Одноразовые процентные скидки на покупку урока или пакета. Код можно задать
          самостоятельно или сгенерировать автоматически.
        </p>
      </header>

      {promoCodes ? (
        <AdminPromoForm promoCodes={promoCodes} />
      ) : (
        <EmptyState
          title="Не удалось загрузить промокоды"
          text="Проверьте, что API запущен, и обновите страницу."
        />
      )}
    </div>
  );
}
