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
    "Индивидуальные уроки фортепиано онлайн для взрослых и детей. Удобный слот в вашем часовом поясе и внимание к звуку.",
  openGraph: {
    type: "website",
    locale: "ru_RU",
    siteName: "Piano School",
    title: "Piano School — фортепиано онлайн",
    description:
      "Индивидуальные уроки фортепиано онлайн. Выбирайте удобное время и занимайтесь в своём темпе.",
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
