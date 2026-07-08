import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HouseFax — due-diligence reports for any home",
  description:
    "AI-generated, source-cited property analysis. A decision-support tool — not financial, legal, or real-estate advice.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="site-header no-print">
          <div className="container header-row">
            <span className="logo">
              House<span className="logo-accent">Fax</span>
            </span>
            <span className="tagline">Carfax for houses</span>
          </div>
        </header>
        <main className="container">{children}</main>
        <footer className="site-footer no-print">
          <div className="container">
            HouseFax is a decision-support tool, not financial, legal, or real-estate advice.
          </div>
        </footer>
      </body>
    </html>
  );
}
