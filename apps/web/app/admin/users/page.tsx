import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { fetchWithSession, type User } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Пользователи",
};

const roleLabels: Record<User["role"], string> = {
  student: "Ученик",
  teacher: "Преподаватель",
  admin: "Администратор",
};

async function loadUsers(): Promise<{ users: User[]; error: string | null }> {
  let response: Response;
  try {
    response = await fetchWithSession("/admin/users");
  } catch {
    return { users: [], error: "Сервис временно недоступен." };
  }

  if (response.status === 401) redirect("/login?next=/admin/users");
  if (!response.ok) {
    return { users: [], error: "Не удалось загрузить пользователей." };
  }
  return { users: (await response.json()) as User[], error: null };
}

export default async function AdminUsersPage() {
  const { users, error } = await loadUsers();

  return (
    <div className="panel-page">
      <header className="panel-page-head">
        <p className="eyebrow">Администратор</p>
        <h1>Пользователи</h1>
        <p className="panel-lead">
          Последние 100 аккаунтов. Роли меняются вручную командой
          <code> make role email=... role=admin</code> на этом этапе.
        </p>
      </header>

      {error ? (
        <p className="form-error" role="alert">
          {error}
        </p>
      ) : null}

      {!error && users.length === 0 ? (
        <p className="panel-lead">Пользователей пока нет.</p>
      ) : null}

      {users.length > 0 ? (
        <div className="table-wrap">
          <table className="data-table">
            <caption className="visually-hidden">Список пользователей</caption>
            <thead>
              <tr>
                <th scope="col">Имя</th>
                <th scope="col">Email</th>
                <th scope="col">Роль</th>
                <th scope="col">Часовой пояс</th>
                <th scope="col">Регистрация</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.name}</td>
                  <td>{user.email}</td>
                  <td>{roleLabels[user.role]}</td>
                  <td>{user.timezone}</td>
                  <td>
                    {new Intl.DateTimeFormat("ru-RU", {
                      dateStyle: "medium",
                    }).format(new Date(user.created_at))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
