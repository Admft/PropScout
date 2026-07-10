import Link from "next/link";

export default function NotFound() {
  return (
    <section className="page-card">
      <h1>404 — Page not found</h1>
      <p className="sub">That route doesn&apos;t exist (or the report id expired).</p>
      <Link href="/">Go home</Link>
      {" · "}
      <Link href="/search">Analyze an address</Link>
    </section>
  );
}
