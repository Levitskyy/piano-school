import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // CI уже гоняет pnpm --filter web typecheck; на VPS этот шаг съедал память и ронял деплой.
  typescript: {
    ignoreBuildErrors: true,
  },
  // Локальная сеть: dev-сервер открывается по адресу Windows-хоста.
  // При смене сети обновите IP здесь.
  allowedDevOrigins: [
    "127.0.0.1",
    "localhost",
    "192.168.1.151",
    "172.31.187.85",
  ],
};

export default nextConfig;
