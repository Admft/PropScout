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

      <section className="record-strip container">
        <h2>See the neighborhood, not just the listing.</h2>
        <p>
          Aerial context for comps, flood, and market signals — the same geospatial lens our
          report uses under the hood.
        </p>
        <div className="record-grid">
          <div className="record-cell">
            <p className="rc-fig">parcel R-048291-0006</p>
            <h3>Parcel-level overview</h3>
            <p>Lot lines, zoning, and last-sale history pulled straight from county records.</p>
          </div>
          <div className="record-cell">
            <p className="rc-fig">radius 0.5mi · 6 comps</p>
            <h3>Block and amenity context</h3>
            <p>Comparable sales and price-per-sqft delta for the immediate block, not the zip code.</p>
          </div>
          <div className="record-cell">
            <p className="rc-fig">tract median income cited</p>
            <h3>Established neighborhood fabric</h3>
            <p>Census tract demographics and trend data behind every neighborhood narrative.</p>
          </div>
        </div>
      </section>

      <section className="quote-plate">
        <div className="quote-plate-content container">
          <p className="qp-label">The product, not the pitch</p>
          <h2>Built for the decision, not the scroll.</h2>
          <p>
            Payment math, rental underwriting, comps, and risk flags — every number from
            deterministic tools, every claim cited.
          </p>
          <div className="quote-links">
            <Link href="/pricing">Pricing</Link>
            <Link href="/faq">FAQ</Link>
            <Link href="/login">Sign in</Link>
          </div>
        </div>
      </section>
    </>
  );
}
