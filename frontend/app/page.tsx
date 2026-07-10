import Link from "next/link";
import Image from "next/image";

export default function LandingPage() {
  return (
    <>
      <section className="hero-bleed">
        <Image
          src="/hero-street.jpg"
          alt="Suburban residential street at golden hour"
          fill
          priority
          className="hero-bleed-img"
          sizes="100vw"
        />
        <div className="hero-bleed-shade" />
        <div className="hero-bleed-content">
          <p className="hero-brand">
            House<span>Fax</span>
          </p>
          <h1>Know the house before you buy it.</h1>
          <p className="hero-lead">
            Source-cited due diligence for any residential address — tools calculate, the model
            explains.
          </p>
          <form className="hero-cta" action="/search" method="get">
            <input
              name="address"
              type="text"
              placeholder="123 Main St, Austin, TX 78704"
              aria-label="Property address"
              required
            />
            <button className="primary" type="submit">
              Analyze address
            </button>
          </form>
          <Link href="/sample-report/123-main-street" className="hero-sample">
            See a sample report →
          </Link>
        </div>
      </section>

      <section className="visual-band container">
        <h2>See the neighborhood, not just the listing.</h2>
        <p>
          Aerial context for comps, flood, and market signals — the same geospatial lens our
          report uses under the hood.
        </p>
        <div className="visual-grid">
          <figure>
            <Image
              src="/aerial-grid.jpg"
              alt="Top-down aerial of a suburban neighborhood"
              width={900}
              height={506}
              className="visual-img"
            />
            <figcaption>Parcel-level overview</figcaption>
          </figure>
          <figure>
            <Image
              src="/aerial-pools.jpg"
              alt="Aerial view of homes with pools and terracotta roofs"
              width={900}
              height={506}
              className="visual-img"
            />
            <figcaption>Block and amenity context</figcaption>
          </figure>
          <figure>
            <Image
              src="/aerial-roofs.jpg"
              alt="Dense residential rooftops among trees at golden hour"
              width={900}
              height={598}
              className="visual-img"
            />
            <figcaption>Established neighborhood fabric</figcaption>
          </figure>
        </div>
      </section>

      <section className="mood-band">
        <Image
          src="/neighborhood-mood.jpg"
          alt=""
          fill
          className="mood-band-img"
          sizes="100vw"
        />
        <div className="mood-band-shade" />
        <div className="mood-band-content container">
          <h2>Built for the decision, not the scroll.</h2>
          <p>
            Payment math, rental underwriting, comps, and risk flags — every number from
            deterministic tools, every claim cited.
          </p>
          <div className="mood-links">
            <Link href="/pricing">Pricing</Link>
            <Link href="/faq">FAQ</Link>
            <Link href="/login">Sign in</Link>
          </div>
        </div>
      </section>
    </>
  );
}
