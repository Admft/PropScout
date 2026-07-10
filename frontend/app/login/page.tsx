"use client";

import { Suspense } from "react";
import Image from "next/image";
import AuthForm from "@/components/AuthForm";

function AuthShell({ mode }: { mode: "login" | "signup" }) {
  return (
    <div className="auth-shell">
      <Image
        src="/aerial-grid.jpg"
        alt=""
        fill
        className="auth-shell-bg"
        sizes="100vw"
        priority
      />
      <div className="auth-shell-shade" />
      <Suspense fallback={<section className="auth-card">Loading…</section>}>
        <AuthForm mode={mode} />
      </Suspense>
    </div>
  );
}

export default function LoginPage() {
  return <AuthShell mode="login" />;
}
