export default function PrivacyPage() {
  return (
    <section className="page-card legal">
      <h1>Privacy Policy</h1>
      <p className="sub">
        Placeholder — replace with Termly / getterms.io generated privacy policy before launch.
      </p>

      <h2>What we collect</h2>
      <ul>
        <li>
          <strong>Identity:</strong> Google account email/name via NextAuth (OAuth). We do not
          receive your Google password.
        </li>
        <li>
          <strong>Usage:</strong> Addresses you analyze, report JSON, profile role, and default
          underwriting assumptions.
        </li>
        <li>
          <strong>Documents:</strong> Files you upload for a property (inspection, disclosure, HOA)
          for document-intelligence processing.
        </li>
      </ul>

      <h2>Payments</h2>
      <p>
        Card payments are processed by <strong>Stripe</strong>. HouseFax does not store full card
        numbers. Stripe&apos;s privacy policy applies to payment data.
      </p>

      <h2>Third parties</h2>
      <ul>
        <li>NextAuth / Google — authentication</li>
        <li>Stripe — billing</li>
        <li>RentCast, Census, FRED, FEMA — property and market data used to build reports</li>
        <li>Anthropic / OpenAI — LLM narrative generation</li>
      </ul>

      <h2>Contact</h2>
      <p>
        Privacy requests: use the <a href="/support">Support</a> form.
      </p>
    </section>
  );
}
