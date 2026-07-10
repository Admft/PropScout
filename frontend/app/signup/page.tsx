"use client";

import { Suspense } from "react";
import Image from "next/image";
import AuthForm from "@/components/AuthForm";

export default function SignupPage() {
  return (
    <div className="auth-shell">
      <Image
        src="/aerial-pools.jpg"
        alt=""
        fill
        className="auth-shell-bg"
        sizes="100vw"
        priority
      />
      <div className="auth-shell-shade" />
      <Suspense fallback={<section className="auth-card">Loading…</section>}>
        <AuthForm mode="signup" />
      </Suspense>
    </div>
  );
}
