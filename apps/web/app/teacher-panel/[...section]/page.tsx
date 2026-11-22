import { EmptyState } from "@/components/empty-state";

const sectionLabels: Record<string, string> = {
  students: "Ученики",
  lessons: "Занятия",
};

type TeacherSectionPageProps = {
  params: Promise<{ section: string[] }>;
};

export default async function TeacherSectionPage({
  params,
}: TeacherSectionPageProps) {
  const { section } = await params;
  const title = sectionLabels[section[0]] ?? "Раздел преподавателя";

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Преподаватель</p>
        <h1>{title}</h1>
      </header>

      <EmptyState
        title="Раздел готовится"
        text="Данные по индивидуальным занятиям появятся на следующем этапе. Сейчас панель доступна только преподавателю и администратору."
      />
    </div>
  );
}
