import type { Metadata } from "next";
import Link from "next/link";
import Image from "next/image";
import LandingEffects from "@/components/LandingEffects";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://housefax.ai";

export const metadata: Metadata = {
  title: {
    absolute: "HouseFax — Know the house before you buy it",
  },
  description:
    "Source-cited due diligence reports for any residential address. Deterministic tools calculate payments, comps, and risk; the model explains with citations. Decision support — not advice.",
  keywords: [
    "HouseFax",
    "property due diligence",
    "home buying report",
    "AVM analysis",
    "comparable sales",
    "rental underwriting",
    "flood risk",
    "source-cited property report",
  ],
  alternates: {
    canonical: "/",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
      "max-video-preview": -1,
    },
  },
  openGraph: {
    type: "website",
    url: SITE_URL,
    siteName: "HouseFax",
    title: "HouseFax — Know the house before you buy it",
    description:
      "Source-cited due diligence for any residential address. Tools calculate. The model explains.",
    images: [
      {
        url: "/opengraph-image",
        width: 1200,
        height: 630,
        alt: "HouseFax — source-cited due diligence reports for residential property",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "HouseFax — Know the house before you buy it",
    description:
      "Source-cited due diligence for any residential address. Tools calculate. The model explains.",
    images: ["/opengraph-image"],
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": `${SITE_URL}/#organization`,
      name: "HouseFax",
      url: SITE_URL,
      logo: `${SITE_URL}/logo.png`,
      description:
        "HouseFax produces source-cited due-diligence reports for residential property buyers and investors.",
      sameAs: [],
    },
    {
      "@type": "WebSite",
      "@id": `${SITE_URL}/#website`,
      url: SITE_URL,
      name: "HouseFax",
      publisher: { "@id": `${SITE_URL}/#organization` },
      potentialAction: {
        "@type": "SearchAction",
        target: {
          "@type": "EntryPoint",
          urlTemplate: `${SITE_URL}/search?address={search_term_string}`,
        },
        "query-input": "required name=search_term_string",
      },
    },
    {
      "@type": "SoftwareApplication",
      "@id": `${SITE_URL}/#app`,
      name: "HouseFax",
      applicationCategory: "BusinessApplication",
      operatingSystem: "Web",
      url: SITE_URL,
      description:
        "AI-assisted property due-diligence platform. Deterministic calculators produce payments, NOI, cap rate, and cash-on-cash; an LLM drafts cited narrative sections. Eval harness checks math, citations, and fair-housing language before a report ships.",
      offers: [
        {
          "@type": "Offer",
          name: "Pay per report",
          price: "9.00",
          priceCurrency: "USD",
          description: "1 report credit. No subscription.",
        },
        {
          "@type": "Offer",
          name: "5-report pack",
          price: "35.00",
          priceCurrency: "USD",
          description: "Best for agents running a few deals a month.",
        },
        {
          "@type": "Offer",
          name: "Pro monthly",
          price: "49.00",
          priceCurrency: "USD",
          description: "20 reports per month.",
        },
      ],
      featureList: [
        "Source-cited narrative sections",
        "Deterministic mortgage and underwriting calculators",
        "Comparable sales and $/sqft analysis",
        "Census tract and flood-zone context",
        "Pre-ship eval harness for math and citation checks",
      ],
      provider: { "@id": `${SITE_URL}/#organization` },
    },
  ],
};

const LENS = [
  {
    key: "parcel",
    fig: "parcel R-048291-0006",
    title: "Parcel-level overview",
    body: "Lot lines, zoning, and last-sale history pulled straight from county records — the legal object, not the listing copy.",
    image: "/aerial-roofs.jpg",
    alt: "Aerial view of residential rooftops used to illustrate parcel-level property context",
  },
  {
    key: "block",
    fig: "radius 0.5mi · 6 comps",
    title: "Block and amenity context",
    body: "Comparable sales and price-per-sqft delta for the immediate block, not the zip code average.",
    image: "/aerial-pools.jpg",
    alt: "Aerial view of neighborhood blocks with pools showing local comparable-sale context",
  },
  {
    key: "fabric",
    fig: "tract median income cited",
    title: "Established neighborhood fabric",
    body: "Census tract demographics and trend data behind every neighborhood narrative — cited, not vibes.",
    image: "/aerial-grid.jpg",
    alt: "Aerial street grid showing neighborhood fabric and census-tract scale context",
  },
] as const;

const STEPS = [
  {
    n: "01",
    title: "Address in",
    body: "Enter any residential address. Optional purchase price, down payment, and buyer-vs-investor intent tune the underwriting.",
  },
  {
    n: "02",
    title: "Tools pull data",
    body: "RentCast facts and AVM, Census ACS, FRED mortgage rate, FEMA flood zone — cached, metered, and grounded in the report.",
  },
  {
    n: "03",
    title: "Model drafts a cited narrative",
    body: "Deterministic tools compute payments and returns. The model narrates with inline source ids — it never invents the math.",
  },
  {
    n: "04",
    title: "Verdict out",
    body: "An eval harness checks math, citations, comps, and fair-housing language before the report ships.",
  },
] as const;

export default function LandingPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <LandingEffects />

      <section className="hero-bleed" aria-labelledby="hero-headline">
        <div className="hero-bleed-media" data-parallax>
          <Image
            src="/hero-street.jpg"
            alt="Tree-lined suburban residential street at golden hour"
            fill
            priority
            quality={70}
            className="hero-bleed-img"
            sizes="100vw"
          />
        </div>
        <div className="hero-bleed-shade" aria-hidden="true" />
        <div className="hero-bleed-grain" aria-hidden="true" />
        <div className="hero-bleed-content">
          <p className="hero-brand" data-hero-enter="1">
            House<span>Fax</span>
          </p>
          <h1 id="hero-headline" data-hero-enter="2">
            Know the house before you buy it.
          </h1>
          <p className="hero-lead" data-hero-enter="3">
            Source-cited due diligence for any residential address — tools calculate, the model
            explains.
          </p>
          <form className="hero-cta" action="/search" method="get" data-hero-enter="4">
            <div className="hero-field">
              <label htmlFor="hero-address">Property address</label>
              <input
                id="hero-address"
                name="address"
                type="text"
                placeholder="123 Main St, Austin, TX 78704"
                autoComplete="street-address"
                required
              />
            </div>
            <button className="primary hero-submit" type="submit">
              Analyze address
            </button>
          </form>
          <Link href="/sample-report/123-main-street" className="hero-sample" data-hero-enter="5">
            See a sample report →
          </Link>
        </div>
      </section>

      <section className="lens-section" aria-labelledby="lens-heading">
        <div className="container">
          <h2 id="lens-heading" data-reveal>
            See the neighborhood, not just the listing.
          </h2>
          <p className="lens-lead" data-reveal>
            Aerial context for comps, flood, and market signals — the same geospatial lens our
            report uses under the hood.
          </p>
          <ul className="lens-list">
            {LENS.map((item, i) => (
              <li
                key={item.key}
                className={`lens-item lens-item--${item.key}`}
                data-reveal
                style={{ ["--reveal-delay" as string]: `${i * 80}ms` }}
              >
                <figure className="lens-figure">
                  <Image
                    src={item.image}
                    alt={item.alt}
                    fill
                    quality={65}
                    sizes="(max-width: 720px) 100vw, 440px"
                    className="lens-img"
                  />
                </figure>
                <div className="lens-copy">
                  <p className="lens-fig">{item.fig}</p>
                  <h3>{item.title}</h3>
                  <p>{item.body}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="how-section" aria-labelledby="how-heading">
        <div className="container">
          <p className="how-kicker" data-reveal>
            Pipeline
          </p>
          <h2 id="how-heading" data-reveal>
            How a report gets made
          </h2>
          <p className="how-lead" data-reveal>
            A fixed sequence — not a black box. Address in, tools out, cited narrative, then a
            machine-checked verdict.
          </p>
          <ol className="how-steps">
            {STEPS.map((step, i) => (
              <li
                key={step.n}
                className="how-step"
                data-reveal
                style={{ ["--reveal-delay" as string]: `${i * 70}ms` }}
              >
                <span className="how-num" aria-hidden="true">
                  {step.n}
                </span>
                <div className="how-step-body">
                  <h3>{step.title}</h3>
                  <p>{step.body}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="quote-plate" aria-labelledby="product-heading">
        <div className="quote-plate-content container" data-reveal>
          <p className="qp-label">The product, not the pitch</p>
          <h2 id="product-heading">Built for the decision, not the scroll.</h2>
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

      <section className="final-cta" aria-labelledby="final-cta-heading">
        <div className="container final-cta-inner" data-reveal>
          <h2 id="final-cta-heading">Run the address.</h2>
          <p>
            One search starts a full due-diligence pass — facts, math, citations, and a checked
            verdict.
          </p>
          <form className="final-cta-form" action="/search" method="get">
            <div className="final-field">
              <label htmlFor="final-address">Property address</label>
              <input
                id="final-address"
                name="address"
                type="text"
                placeholder="123 Main St, Austin, TX 78704"
                autoComplete="street-address"
                required
              />
            </div>
            <button className="primary final-submit" type="submit">
              Analyze address
            </button>
          </form>
          <Link href="/sample-report/123-main-street" className="final-sample">
            Or open the sample report →
          </Link>
        </div>
      </section>
    </>
  );
}
