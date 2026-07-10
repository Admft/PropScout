"use client";

import { Suspense } from "react";
import AuthForm from "@/components/AuthForm";

export default function LoginPage() {
  return (
    <div className="auth-shell">
      <Suspense fallback={<section className="auth-card">Loading…</section>}>
        <AuthForm mode="login" />
      </Suspense>
    </div>
  );
}
