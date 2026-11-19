"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function LogoutButton() {
  const router = useRouter();
  const [pending, setPending] = useState(false);

  async function handleLogout() {
    setPending(true);
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } finally {
      router.push("/");
      router.refresh();
    }
  }

  return (
    <button
      className="button button-ghost button-small"
      type="button"
      onClick={handleLogout}
      disabled={pending}
    >
      {pending ? "Выходим…" : "Выйти"}
    </button>
  );
}
