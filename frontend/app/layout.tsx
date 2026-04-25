import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "react-hot-toast";
import { AuthProvider } from "@/lib/auth-context";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "SportShield — AI-Powered Sports Media Protection",
  description: "Protect your sports media assets from piracy with AI-powered digital fingerprinting.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans antialiased`}>
        <AuthProvider>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: "#1a1a2e",
                color: "#e2e8f0",
                border: "1px solid rgba(99, 102, 241, 0.3)",
              },
            }}
          />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
