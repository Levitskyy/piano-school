import type { Metadata } from "next";

import { AdminPromoForm } from "@/components/admin-promo-form";
import { EmptyState } from "@/components/empty-state";
import { fetchWithSession } from "@/lib/auth";
import type { IndividualLessonOffer } from "@/lib/individual-lessons-shared";

export const metadata: Metadata = {
  title: "Промокоды",
};

type PromoCode = {
  id: string;
  code: string;
  discount_percent: string | number;
  offer_id: string | null;
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

async function loadOffers(): Promise<IndividualLessonOffer[] | null> {
  try {
    const response = await fetchWithSession("/admin/products");
    if (!response.ok) return null;
    return (await response.json()) as IndividualLessonOffer[];
  } catch {
    return null;
  }
}

export default async function AdminPromoCodesPage() {
  const [promoCodes, offers] = await Promise.all([loadPromoCodes(), loadOffers()]);

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Администратор</p>
        <h1>Промокоды</h1>
        <p className="panel-lead">
          Одноразовые процентные скидки на выбранный тариф: разовый урок или пакет. Код можно
          задать самостоятельно или сгенерировать автоматически.
        </p>
      </header>

      {promoCodes && offers ? (
        <AdminPromoForm promoCodes={promoCodes} offers={offers} />
      ) : (
        <EmptyState
          title="Не удалось загрузить промокоды и тарифы"
          text="Проверьте, что API запущен, и обновите страницу."
        />
      )}
    </div>
  );
}
