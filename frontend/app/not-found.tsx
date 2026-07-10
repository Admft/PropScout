import Link from "next/link";
import Stamp from "@/components/Stamp";

export default function NotFound() {
  return (
    <section className="page-card">
      <div className="verdict-row">
        <Stamp variant="failed" text="Not on file" size="sm" />
      </div>
      <h1>Record not found</h1>
      <p className="sub">That route doesn&apos;t exist (or the report id expired).</p>
      <Link href="/">Go home</Link>
      {" · "}
      <Link href="/search">Analyze an address</Link>
    </section>
  );
}
