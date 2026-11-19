import type { NextRequest } from "next/server";

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

export const dynamic = "force-dynamic";

type RouteContext = { params: Promise<{ path: string[] }> };

async function proxy(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const target = new URL(path.map(encodeURIComponent).join("/"), `${API_URL}/`);
  target.search = request.nextUrl.search;

  const headers = new Headers();
  for (const name of [
    "accept",
    "accept-language",
    "content-type",
    "cookie",
    "user-agent",
    "x-forwarded-for",
  ]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  const contentType = request.headers.get("content-type") ?? "";
  const isAuthForm =
    request.method === "POST" &&
    contentType.includes("application/x-www-form-urlencoded") &&
    path[0] === "auth" &&
    (path[1] === "login" || path[1] === "register");

  let body: ArrayBuffer | string | undefined;
  if (request.method !== "GET" && request.method !== "HEAD") {
    if (isAuthForm) {
      const form = await request.formData();
      const payload: Record<string, string> = {};
      for (const [key, value] of form.entries()) {
        if (typeof value === "string") payload[key] = value;
      }
      body = JSON.stringify(payload);
      headers.set("content-type", "application/json");
    } else {
      body = await request.arrayBuffer();
    }
  }

  try {
    const upstream = await fetch(target, {
      method: request.method,
      headers,
      body,
      redirect: "manual",
      cache: "no-store",
    });

    const responseHeaders = new Headers();
    for (const name of ["cache-control", "content-type", "location"]) {
      const value = upstream.headers.get(name);
      if (value) responseHeaders.set(name, value);
    }

    const setCookies = upstream.headers.getSetCookie?.() ?? [];
    if (setCookies.length > 0) {
      for (const cookie of setCookies) {
        responseHeaders.append("set-cookie", cookie);
      }
    } else {
      const cookie = upstream.headers.get("set-cookie");
      if (cookie) responseHeaders.append("set-cookie", cookie);
    }

    if (
      isAuthForm &&
      upstream.ok &&
      request.headers.get("accept")?.includes("text/html")
    ) {
      responseHeaders.set("location", "/account");
      return new Response(null, { status: 303, headers: responseHeaders });
    }

    return new Response(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch {
    return Response.json(
      { detail: "Сервис временно недоступен. Попробуйте ещё раз." },
      { status: 503 },
    );
  }
}

export function GET(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export function POST(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export function PUT(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export function PATCH(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export function DELETE(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export function HEAD(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export function OPTIONS(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}
