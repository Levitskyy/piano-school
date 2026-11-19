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
    default: "Piano School — фортепиано онлайн",
    template: "%s — Piano School",
  },
  description:
    "Онлайн-курс и индивидуальные уроки фортепиано для взрослых и детей. Понятная программа, ноты и внимание к звуку.",
  openGraph: {
    type: "website",
    locale: "ru_RU",
    siteName: "Piano School",
    title: "Piano School — фортепиано онлайн",
    description:
      "Онлайн-курс и индивидуальные уроки фортепиано. Понятная программа, ноты и внимание к звуку.",
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
