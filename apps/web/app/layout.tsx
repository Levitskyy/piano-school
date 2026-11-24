import type { Metadata } from "next";
import { Cormorant_Garamond, Inter } from "next/font/google";

import "./globals.css";

const serif = Cormorant_Garamond({
  subsets: ["cyrillic", "latin"],
  weight: ["400", "500", "600"],
  variable: "--font-serif",
  display: "swap",
});

const sans = Inter({
  subsets: ["cyrillic", "latin"],
  weight: ["400", "500"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Levickaya Piano — фортепиано онлайн",
    template: "%s — Levickaya Piano",
  },
  description:
    "Индивидуальные уроки фортепиано онлайн с Ларисой Валентиновной. Классическая школа, живая музыка, удобный слот в вашем часовом поясе.",
  openGraph: {
    type: "website",
    locale: "ru_RU",
    siteName: "Levickaya Piano",
    title: "Levickaya Piano — фортепиано онлайн",
    description:
      "Классическая школа. Живая музыка. Индивидуальные уроки фортепиано онлайн с Ларисой Валентиновной.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" className={`${serif.variable} ${sans.variable}`}>
      <body>{children}</body>
    </html>
  );
}
