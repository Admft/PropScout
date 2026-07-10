"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <section className="page-card">
      <h1>Something went wrong</h1>
      <p className="sub">{error.message || "Unexpected error"}</p>
      <button className="primary" type="button" onClick={() => reset()}>
        Try again
      </button>
    </section>
  );
}
