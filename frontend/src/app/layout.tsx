import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { SiteHeader } from "@/components/layout/site-header";
import { SkipLink } from "@/components/layout/skip-link";
import { ThemeScript } from "@/components/theme/theme-script";
import { isMockingEnabled } from "@/mocks/is-mocking-enabled";
import { MockProvider } from "@/mocks/provider";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "MarketPilot",
  description: "Autonomous advertising creative pipeline",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  const main = (
    <main id="main-content" tabIndex={-1} className="flex-1">
      {children}
    </main>
  );

  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <ThemeScript />
      </head>
      <body className="flex min-h-full flex-col">
        <SkipLink />
        <SiteHeader />
        {isMockingEnabled() ? <MockProvider>{main}</MockProvider> : main}
      </body>
    </html>
  );
}
