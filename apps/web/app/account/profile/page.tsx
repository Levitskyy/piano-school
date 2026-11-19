import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { ProfileForm } from "@/components/profile-form";
import { getCurrentUser } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Профиль",
};

export default async function ProfilePage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/account/profile");

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Аккаунт</p>
        <h1>Профиль</h1>
        <p className="panel-lead">
          Имя и часовой пояс нужны для расписания и обратной связи. Остальные данные
          можно будет добавить позже.
        </p>
      </header>

      <section className="panel-section" aria-labelledby="profile-form-title">
        <div className="panel-section-head">
          <h2 id="profile-form-title">Личные данные</h2>
        </div>
        <ProfileForm
          initialName={user.name}
          initialTimezone={user.timezone}
          email={user.email}
        />
      </section>
    </div>
  );
}
