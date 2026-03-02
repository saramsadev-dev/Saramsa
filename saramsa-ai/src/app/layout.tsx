// app/layout.tsx
import type { Metadata } from "next";
import { Space_Grotesk, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import StoreProvider from "@/store/StoreProvider";
import { Navbar } from "@/components/ui/navbar";
import { Providers } from "@/components/providers/providers";
import { Toaster } from "sonner";
import { PipelineStatusWidget } from "@/components/ui/pipeline-status-widget";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
});
const ibmPlexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-ibm-plex-mono",
});

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
      <body className={`${spaceGrotesk.className} ${spaceGrotesk.variable} ${ibmPlexMono.variable} flex flex-col min-h-screen`}>
        <Providers>
          <StoreProvider>
            <Navbar/>
            <main className="flex-1 overflow-hidden">{children}</main>
            <PipelineStatusWidget />
            <Toaster 
              position="top-right" 
              richColors 
              duration={2000}
              closeButton
            />
          </StoreProvider>
        </Providers>
      </body>
    </html>
  );
}
