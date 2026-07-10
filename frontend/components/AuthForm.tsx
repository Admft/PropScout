"use client";

import { signIn } from "next-auth/react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

export default function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const params = useSearchParams();
  const callbackUrl = params.get("callbackUrl") || "/welcome";
  const googleReady = Boolean(process.env.NEXT_PUBLIC_GOOGLE_AUTH === "1");

  return (
    <section className="auth-card">
      <h1>{mode === "signup" ? "Create your HouseFax account" : "Sign in to HouseFax"}</h1>
      <p className="sub">
        One account for reports, credits, and saved assumptions. Free to start — pay only when
        you generate a report.
      </p>

      <button
        className="primary google-btn"
        type="button"
        onClick={() => {
          if (googleReady) {
            void signIn("google", { callbackUrl });
          } else {
            window.location.href = callbackUrl;
          }
        }}
      >
        Continue with Google
      </button>

      {!googleReady && (
        <p className="hint">
          Google OAuth is not configured yet. Demo mode continues without a real session.
        </p>
      )}

      <p className="legal-note">
        By continuing, you agree to our <Link href="/terms">Terms of Service</Link> and{" "}
        <Link href="/privacy">Privacy Policy</Link>.
      </p>

      <p className="auth-switch">
        {mode === "login" ? (
          <>
            New here? <Link href="/signup">Create an account</Link>
          </>
        ) : (
          <>
            Already have an account? <Link href="/login">Sign in</Link>
          </>
        )}
      </p>
    </section>
  );
}
