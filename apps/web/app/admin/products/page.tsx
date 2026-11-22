import type { Metadata } from "next";

import { AdminPriceEditor } from "@/components/admin-price-editor";
import { EmptyState } from "@/components/empty-state";
import { fetchWithSession } from "@/lib/auth";
import type { IndividualLessonOffer } from "@/lib/individual-lessons-shared";

export const metadata: Metadata = {
  title: "Цены",
};

async function loadOffers(): Promise<IndividualLessonOffer[] | null> {
  try {
    const response = await fetchWithSession("/admin/products");
    if (!response.ok) return null;
    return (await response.json()) as IndividualLessonOffer[];
  } catch {
    return null;
  }
}

export default async function AdminProductsPage() {
  const offers = await loadOffers();

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Администратор</p>
        <h1>Цены на занятия</h1>
        <p className="panel-lead">
          Стоимость разового урока и пакетов. Изменения сразу видны на странице записи и
          передаются в ЮKassa при оплате.
        </p>
      </header>

      {offers ? (
        <AdminPriceEditor offers={offers} />
      ) : (
        <EmptyState
          title="Не удалось загрузить цены"
          text="Проверьте, что API запущен, и обновите страницу."
        />
      )}
    </div>
  );
}
