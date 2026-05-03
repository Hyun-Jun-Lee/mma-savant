import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { SessionProvider } from "@/components/providers/SessionProvider";
import { GlobalNav } from "@/components/layout/GlobalNav";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "sonner";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "MMA Savant - Your Personal MMA Expert",
  description: "Get expert insights on MMA fighters, techniques, and fight analysis",
  icons: { icon: "/favicon.svg" },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-[#050507] text-zinc-100`}
      >
        <SessionProvider>
          <TooltipProvider>
            <GlobalNav />
            <main>{children}</main>
          </TooltipProvider>
          <Toaster
            theme="dark"
            position="top-center"
            toastOptions={{
              style: {
                background: '#18181b',
                border: '1px solid rgba(255,255,255,0.06)',
                color: '#fafafa',
              },
            }}
            richColors
          />
        </SessionProvider>
      </body>
    </html>
  );
}
