import { NextResponse } from "next/server";

/** Creates a Stripe Customer Portal session URL. */
export async function POST() {
  const secret = process.env.STRIPE_SECRET_KEY;
  const customerId = process.env.STRIPE_DEMO_CUSTOMER_ID;

  if (!secret || !customerId) {
    return NextResponse.json(
      {
        detail:
          "Stripe Customer Portal needs STRIPE_SECRET_KEY and a Stripe customer id (STRIPE_DEMO_CUSTOMER_ID for now).",
      },
      { status: 501 }
    );
  }

  const origin = process.env.NEXTAUTH_URL || "http://localhost:3000";
  const params = new URLSearchParams({
    customer: customerId,
    return_url: `${origin}/settings/billing`,
  });

  const stripeResp = await fetch("https://api.stripe.com/v1/billing_portal/sessions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${secret}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: params,
  });
  const session = await stripeResp.json();
  if (!stripeResp.ok) {
    return NextResponse.json(
      { detail: session.error?.message ?? "Portal session failed" },
      { status: 502 }
    );
  }
  return NextResponse.json({ url: session.url });
}
