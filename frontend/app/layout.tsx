import type { Metadata } from "next";
import { Fraunces, Source_Serif_4, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import SiteNav from "@/components/SiteNav";
import Providers from "@/components/Providers";
import Link from "next/link";

const fraunces = Fraunces({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
  display: "swap",
});

const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-body",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "HouseFax — due-diligence reports for any home",
  description:
    "AI-generated, source-cited property analysis. A decision-support tool — not financial, legal, or real-estate advice.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${fraunces.variable} ${sourceSerif.variable} ${plexMono.variable}`}>
      <body>
        <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden="true">
          <filter id="ink-bleed" x="-20%" y="-20%" width="140%" height="140%">
            <feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves="3" result="noise" seed="7" />
            <feDisplacementMap in="SourceGraphic" in2="noise" scale="7" />
          </filter>
          <filter id="ink-bleed-sm" x="-20%" y="-20%" width="140%" height="140%">
            <feTurbulence type="fractalNoise" baseFrequency="0.09" numOctaves="2" result="noise" seed="4" />
            <feDisplacementMap in="SourceGraphic" in2="noise" scale="3" />
          </filter>
        </svg>
        <Providers>
          <SiteNav />
          <main className="page-main">{children}</main>
          <footer className="site-footer no-print">
            <div className="container footer-grid">
              <p>
                HouseFax is a decision-support tool, not financial, legal, or real-estate advice.
                AVM estimates are models — not appraisals.
              </p>
              <div className="footer-links">
                <Link href="/faq">FAQ</Link>
                <Link href="/pricing">Pricing</Link>
                <Link href="/terms">Terms</Link>
                <Link href="/privacy">Privacy</Link>
                <Link href="/support">Support</Link>
              </div>
            </div>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
