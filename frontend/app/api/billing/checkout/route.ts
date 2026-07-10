import { NextResponse } from "next/server";

/**
 * Creates a Stripe Checkout Session.
 * Requires STRIPE_SECRET_KEY + STRIPE_PRICE_* env vars. Until then, returns a clear message.
 */
export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const tier = (body.tier as string) || "single";
  const secret = process.env.STRIPE_SECRET_KEY;

  if (!secret) {
    return NextResponse.json(
      {
        detail:
          "Stripe is not configured. Add STRIPE_SECRET_KEY and price IDs to enable Checkout.",
      },
      { status: 501 }
    );
  }

  const priceMap: Record<string, string | undefined> = {
    single: process.env.STRIPE_PRICE_SINGLE,
    pack5: process.env.STRIPE_PRICE_PACK5,
    pro: process.env.STRIPE_PRICE_PRO,
  };
  const priceId = priceMap[tier];
  if (!priceId) {
    return NextResponse.json({ detail: `Missing Stripe price for tier: ${tier}` }, { status: 400 });
  }

  const origin = process.env.NEXTAUTH_URL || "http://localhost:3000";
  const params = new URLSearchParams({
    "mode": tier === "pro" ? "subscription" : "payment",
    "success_url": `${origin}/dashboard?checkout=success`,
    "cancel_url": `${origin}/pricing?checkout=cancel`,
    "line_items[0][price]": priceId,
    "line_items[0][quantity]": "1",
  });

  const stripeResp = await fetch("https://api.stripe.com/v1/checkout/sessions", {
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
      { detail: session.error?.message ?? "Stripe Checkout failed" },
      { status: 502 }
    );
  }
  return NextResponse.json({ url: session.url });
}
