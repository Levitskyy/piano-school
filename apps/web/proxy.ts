import { NextResponse } from "next/server";

// Курсовые страницы полностью закрыты до включения флага.
// Proxy отвечает до рендера, поэтому 404 возвращается и для вложенных кабинетов.
export function proxy() {
  if (process.env.COURSES_ENABLED === "false") {
    return new NextResponse("Страница не найдена", {
      status: 404,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/courses/:path*",
    "/account/courses/:path*",
    "/admin/courses/:path*",
  ],
};
