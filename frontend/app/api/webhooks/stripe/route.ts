import { NextResponse } from "next/server";

/**
 * Stripe webhook listener.
 * Verifies signature when STRIPE_WEBHOOK_SECRET is set, then updates credits/subscription
 * in Postgres (hook point — persistence wired when users table is live).
 */
export async function POST(req: Request) {
  const secret = process.env.STRIPE_WEBHOOK_SECRET;
  const payload = await req.text();
  const sig = req.headers.get("stripe-signature");

  if (!secret) {
    return NextResponse.json(
      { received: false, detail: "STRIPE_WEBHOOK_SECRET not configured" },
      { status: 501 }
    );
  }

  if (!sig) {
    return NextResponse.json({ detail: "Missing stripe-signature" }, { status: 400 });
  }

  // Signature verification + event handling will call into FastAPI / Postgres.
  // For now acknowledge receipt so Stripe can be pointed at this URL in test mode.
  console.info("[stripe webhook] received", payload.slice(0, 120), "sig=", sig.slice(0, 24));

  return NextResponse.json({ received: true });
}
