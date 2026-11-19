import { cookies } from "next/headers";
import { cache } from "react";

export const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

export type UserRole = "student" | "teacher" | "admin";

export type User = {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  timezone: string;
  preferred_language: string;
  email_verified_at: string | null;
  created_at: string;
};

export async function fetchCurrentUser(): Promise<User | null> {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  if (!cookieHeader) return null;

  try {
    const response = await fetch(`${API_URL}/auth/me`, {
      headers: { cookie: cookieHeader },
      cache: "no-store",
    });
    if (!response.ok) return null;
    return (await response.json()) as User;
  } catch {
    return null;
  }
}

export const getCurrentUser = cache(fetchCurrentUser);

export async function fetchWithSession(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const cookieStore = await cookies();
  const headers = new Headers(init.headers);
  if (cookieStore.size > 0) headers.set("cookie", cookieStore.toString());

  return fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
}
