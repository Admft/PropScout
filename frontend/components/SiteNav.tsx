"use client";

import Link from "next/link";
import Image from "next/image";
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
          <Image
            src="/aerial-roofs.jpg"
            alt=""
            width={28}
            height={28}
            className="logo-mark"
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
