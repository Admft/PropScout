"use client";

import { Suspense } from "react";
import AuthForm from "@/components/AuthForm";

export default function SignupPage() {
  return (
    <div className="auth-shell">
      <Suspense fallback={<section className="auth-card">Loading…</section>}>
        <AuthForm mode="signup" />
      </Suspense>
    </div>
  );
}
