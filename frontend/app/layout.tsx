import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Career Discovery - Find Your Ideal Career Path",
  description: "Discover your ideal career path through our AI-powered questionnaire",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full bg-[#f8fafc] text-[#0f172a]" style={{ colorScheme: "light" }}>
      <body className="min-h-full antialiased bg-[#f8fafc] text-[#0f172a]">
        {children}
      </body>
    </html>
  );
}


