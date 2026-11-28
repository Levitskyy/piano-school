import type { Metadata } from "next";

import { AdminOfferEditor } from "@/components/admin-offer-editor";
import { EmptyState } from "@/components/empty-state";
import { fetchWithSession } from "@/lib/auth";
import type { IndividualLessonOffer } from "@/lib/individual-lessons-shared";

type AdminOffer = IndividualLessonOffer & {
  is_active: boolean;
  position: number;
};

export const metadata: Metadata = {
  title: "Тарифы на занятия",
};

async function loadOffers(): Promise<AdminOffer[] | null> {
  try {
    const response = await fetchWithSession("/admin/products");
    if (!response.ok) return null;
    return (await response.json()) as AdminOffer[];
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
        <h1>Тарифы на занятия</h1>
        <p className="panel-lead">
          Разовый урок и пакеты занятий: название, описание, количество уроков, цена и срок
          действия. Изменения сразу видны на странице записи и передаются в платёжную систему.
        </p>
      </header>

      {offers ? (
        <AdminOfferEditor offers={offers} />
      ) : (
        <EmptyState
          title="Не удалось загрузить тарифы"
          text="Проверьте, что API запущен, и обновите страницу."
        />
      )}
    </div>
  );
}
