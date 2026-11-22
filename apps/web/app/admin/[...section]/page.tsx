import { notFound } from "next/navigation";

import { EmptyState } from "@/components/empty-state";
import { coursesEnabled } from "@/lib/feature-flags";

const sectionLabels: Record<string, string> = {
  courses: "Курсы",
  products: "Продукты",
  orders: "Заказы",
  settings: "Настройки",
};

type AdminSectionPageProps = {
  params: Promise<{ section: string[] }>;
};

export default async function AdminSectionPage({ params }: AdminSectionPageProps) {
  const { section } = await params;
  if (!coursesEnabled && section[0] === "courses") notFound();
  const title = sectionLabels[section[0]] ?? "Раздел администратора";

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Администратор</p>
        <h1>{title}</h1>
      </header>

      <EmptyState
        title="Раздел готовится"
        text="Управление появится на следующем этапе вместе с моделями продуктов и заказов."
      />
    </div>
  );
}
