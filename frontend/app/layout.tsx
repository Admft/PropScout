import type { Metadata } from "next";
import "./globals.css";
import SiteNav from "@/components/SiteNav";
import Providers from "@/components/Providers";
import Link from "next/link";

export const metadata: Metadata = {
  title: "HouseFax — due-diligence reports for any home",
  description:
    "AI-generated, source-cited property analysis. A decision-support tool — not financial, legal, or real-estate advice.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
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
