import Link from "next/link";

import { EmptyState } from "@/components/empty-state";

const sectionLabels: Record<string, string> = {
  "individual-lessons": "Индивидуальные занятия",
  profile: "Профиль",
};

type AccountSectionPageProps = {
  params: Promise<{ section: string[] }>;
};

export default async function AccountSectionPage({
  params,
}: AccountSectionPageProps) {
  const { section } = await params;
  const title = sectionLabels[section[0]] ?? "Раздел кабинета";

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Личный кабинет</p>
        <h1>{title}</h1>
      </header>

      <EmptyState
        title="Раздел готовится"
        text="Здесь появятся данные по занятиям и профилю. Пока вход, роли и защита кабинета уже работают."
        action={
          <Link className="button" href="/individual-lessons">
            Выбрать занятие
          </Link>
        }
      />
    </div>
  );
}
