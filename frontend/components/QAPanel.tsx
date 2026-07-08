"use client";

import { useState } from "react";
import { askQuestion } from "@/lib/api";

interface Exchange {
  question: string;
  answer: string;
}

export default function QAPanel({ reportId }: { reportId: string }) {
  const [question, setQuestion] = useState("");
  const [thread, setThread] = useState<Exchange[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onAsk(e: React.FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await askQuestion(reportId, q);
      setThread((t) => [...t, { question: q, answer: resp.answer }]);
      setQuestion("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card no-print" style={{ marginTop: 18 }}>
      <h2>Ask a follow-up</h2>
      <div className="qa-thread">
        {thread.map((ex, i) => (
          <div key={i} style={{ display: "contents" }}>
            <div className="qa-q">{ex.question}</div>
            <div className="qa-a">{ex.answer}</div>
          </div>
        ))}
      </div>
      <form className="qa-form" onSubmit={onAsk}>
        <input
          placeholder='e.g. "What would the payment be with 10% down?"'
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={loading}
        />
        <button className="primary" style={{ marginTop: 0 }} type="submit" disabled={loading}>
          {loading ? "Thinking…" : "Ask"}
        </button>
      </form>
      {error && <div className="error-box">{error}</div>}
    </section>
  );
}
