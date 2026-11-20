"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

type ClientRedirectProps = {
  to: string;
};

export function ClientRedirect({ to }: ClientRedirectProps) {
  const router = useRouter();

  useEffect(() => {
    router.replace(to);
  }, [router, to]);

  return (
    <main className="redirect-page" id="main-heading">
      <p className="eyebrow">Перенаправление</p>
      <h1>Подождите</h1>
      <p className="panel-lead">
        Переходим на нужную страницу. Если это не произошло, воспользуйтесь
        ссылкой ниже.
      </p>
      <Link className="button" href={to}>
        Продолжить
      </Link>
    </main>
  );
}
