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

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://housefax.ai";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "HouseFax — due-diligence reports for any home",
    template: "%s · HouseFax",
  },
  description:
    "AI-generated, source-cited property analysis. A decision-support tool — not financial, legal, or real-estate advice.",
  applicationName: "HouseFax",
  authors: [{ name: "HouseFax" }],
  creator: "HouseFax",
  openGraph: {
    type: "website",
    siteName: "HouseFax",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
  },
  robots: {
    index: true,
    follow: true,
  },
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
          <main id="main-content" className="page-main">
            {children}
          </main>
          <footer className="site-footer no-print" aria-label="Site">
            <div className="container footer-grid">
              <p>
                HouseFax is a decision-support tool, not financial, legal, or real-estate advice.
                AVM estimates are models — not appraisals.
              </p>
              <nav className="footer-links" aria-label="Footer">
                <Link href="/faq">FAQ</Link>
                <Link href="/pricing">Pricing</Link>
                <Link href="/terms">Terms</Link>
                <Link href="/privacy">Privacy</Link>
                <Link href="/support">Support</Link>
              </nav>
            </div>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
