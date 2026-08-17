import type { Metadata } from "next";
import { Figtree } from "next/font/google";
import "./globals.css";

const figtree = Figtree({
  variable: "--font-figtree",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Tatvic - GA4 PII Auditor",
  description: "Monitor and detect Personally Identifiable Information leaks across your Google Analytics 4 properties.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${figtree.variable} font-sans h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-background text-brand-body">{children}</body>
    </html>
  );
}
