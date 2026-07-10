"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/search", label: "Search" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/pricing", label: "Pricing" },
  { href: "/faq", label: "FAQ" },
];

export default function SiteNav() {
  const pathname = usePathname();
  const onHero = pathname === "/";

  return (
    <nav
      className={onHero ? "site-nav site-nav-over no-print" : "site-nav no-print"}
      aria-label="Primary"
    >
      <div className="container header-row">
        <Link href="/" className="logo logo-with-mark">
          <img
            src="/logo.png"
            alt=""
            className="logo-seal"
            width={24}
            height={24}
            aria-hidden="true"
          />
          House<span className="logo-accent">Fax</span>
        </Link>
        <div className="nav-links">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={pathname?.startsWith(l.href) ? "nav-link active" : "nav-link"}
            >
              {l.label}
            </Link>
          ))}
          <Link href="/settings/profile" className="nav-link">
            Settings
          </Link>
          <Link href="/login" className="nav-cta">
            Sign in
          </Link>
        </div>
      </div>
    </nav>
  );
}
