import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tatvic - GA4 PII Auditor",
  description: "Monitor and detect Personally Identifiable Information leaks across your Google Analytics 4 properties.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="font-sans h-full antialiased">
      <body className="min-h-full flex flex-col bg-background text-brand-body">{children}</body>
    </html>
  );
}
