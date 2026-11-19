import { EmptyState } from "@/components/empty-state";

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
  const title = sectionLabels[section[0]] ?? "Раздел администратора";

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Администратор</p>
        <h1>{title}</h1>
      </header>

      <EmptyState
        title="Раздел готовится"
        text="Управление появится на следующем этапе вместе с моделями курсов, продуктов и заказов."
      />
    </div>
  );
}
