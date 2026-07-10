export default function TermsPage() {
  return (
    <section className="page-card legal">
      <h1>Terms of Service</h1>
      <p className="sub">
        Placeholder — replace with Termly / getterms.io generated terms before production launch.
      </p>

      <h2>IMPORTANT DISCLAIMERS</h2>
      <div className="disclaimer-box">
        <p>
          <strong>NOT AN APPRAISAL.</strong> AUTOMATED VALUATION MODEL (AVM) ESTIMATES ARE
          STATISTICAL MODELS ONLY. THEY ARE NOT APPRAISALS AND MUST NOT BE RELIED UPON AS A
          SUBSTITUTE FOR A LICENSED APPRAISAL, INSPECTION, OR PROFESSIONAL ADVICE.
        </p>
        <p>
          <strong>NOT FINANCIAL, LEGAL, OR REAL-ESTATE ADVICE.</strong> HOUSEFAX IS A
          DECISION-SUPPORT TOOL. VERDICTS SUCH AS &quot;CAUTIOUS BUY&quot; OR &quot;PASS&quot; ARE
          INFORMATIONAL ONLY AND DO NOT GUARANTEE INVESTMENT PERFORMANCE OR APPRECIATION.
        </p>
        <p>
          <strong>NO WARRANTY.</strong> DATA FROM THIRD-PARTY PROVIDERS (RENTCAST, CENSUS, FRED,
          FEMA, AND OTHERS) MAY BE INCOMPLETE, DELAYED, OR INACCURATE. YOU ASSUME ALL RISK FOR
          DECISIONS MADE USING THIS SERVICE.
        </p>
      </div>

      <h2>Acceptable use</h2>
      <p>
        You may not use HouseFax to discriminate in housing decisions in violation of the Fair
        Housing Act or equivalent law. Reports are generated with fair-housing language checks;
        circumventing those checks is prohibited.
      </p>

      <h2>Payments</h2>
      <p>
        Report credits and subscriptions are billed via Stripe. Refund policy is described on the
        FAQ and Support pages.
      </p>
    </section>
  );
}
