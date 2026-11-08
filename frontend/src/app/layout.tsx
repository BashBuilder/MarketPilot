import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
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
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <MockProvider>{children}</MockProvider>
      </body>
    </html>
  );
}
