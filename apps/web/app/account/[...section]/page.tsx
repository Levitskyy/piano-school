import { ClientRedirect } from "@/components/client-redirect";
import { EmptyState } from "@/components/empty-state";

const sectionLabels: Record<string, string> = {
  "individual-lessons": "Индивидуальные занятия",
  orders: "Заказы",
};

const mergedSections = new Set(["submissions", "mentorship"]);

type AccountSectionPageProps = {
  params: Promise<{ section: string[] }>;
};

export default async function AccountSectionPage({
  params,
}: AccountSectionPageProps) {
  const { section } = await params;
  const key = section[0];

  if (mergedSections.has(key)) {
    return <ClientRedirect to="/account/courses" />;
  }

  const title = sectionLabels[key] ?? "Раздел кабинета";

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Личный кабинет</p>
        <h1>{title}</h1>
      </header>

      <EmptyState
        title="Раздел готовится"
        text="Функциональность появится на следующем этапе. Сейчас важно, что вход, роли и защита кабинета уже работают."
      />
    </div>
  );
}
