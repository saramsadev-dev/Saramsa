// app/layout.tsx
import type { Metadata } from "next";
import { Space_Grotesk, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import StoreProvider from "@/store/StoreProvider";
import { Navbar } from "@/components/ui/navbar";
import { Providers } from "@/components/providers/providers";
import { Toaster } from "sonner";
import { PipelineWidgetGate } from "@/components/ui/pipeline-widget-gate";
import { ErrorBoundary } from "@/components/ErrorBoundary";

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
  title: "Saramsa.ai",
  description: "AI-powered content analysis platform",
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/favicon.ico", sizes: "any" },
    ],
    shortcut: "/favicon.svg",
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
      <body className={`${spaceGrotesk.className} ${spaceGrotesk.variable} ${ibmPlexMono.variable} flex flex-col h-screen`}>
        <Providers>
          <StoreProvider>
            <ErrorBoundary>
              <Navbar/>
              <main className="flex-1 overflow-hidden">{children}</main>
              <PipelineWidgetGate />
            </ErrorBoundary>
            <Toaster
              position="bottom-right"
              duration={2000}
              closeButton
              theme="system"
              toastOptions={{
                classNames: {
                  toast: 'bg-background border-border',
                  title: 'text-foreground',
                  description: 'text-muted-foreground',
                  actionButton: 'bg-saramsa-brand text-white hover:bg-saramsa-brand-hover',
                  cancelButton: 'bg-muted text-muted-foreground',
                  closeButton: 'bg-background border-border text-foreground',
                },
              }}
            />
          </StoreProvider>
        </Providers>
      </body>
    </html>
  );
}
