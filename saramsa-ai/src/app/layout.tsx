// app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import StoreProvider from "@/store/StoreProvider";
import { Navbar } from "@/components/ui/navbar";
import { Providers } from "@/components/providers/providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Saramsa AI",
  description: "AI-powered content analysis platform",
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon.ico",
    apple: "/apple-icon.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} flex flex-col min-h-screen`}>
        <Providers>
          <StoreProvider>
            <Navbar/>
            <main className="flex-1 overflow-hidden">{children}</main>
          </StoreProvider>
        </Providers>
      </body>
    </html>
  );
}
