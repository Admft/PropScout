export default function SupportPage() {
  return (
    <section className="page-card">
      <h1>Support</h1>
      <p className="sub">
        Bug reports, refund requests, and account help. Embed a free{" "}
        <a href="https://tally.so" target="_blank" rel="noreferrer">
          Tally.so
        </a>{" "}
        form here in production — the form below is a local stand-in that opens your mail client.
      </p>

      <form
        className="form-stack"
        action="mailto:support@housefax.example"
        method="get"
        encType="text/plain"
      >
        <div>
          <label htmlFor="topic">Topic</label>
          <select id="topic" name="subject" defaultValue="Bug report">
            <option>Bug report</option>
            <option>Refund request</option>
            <option>Account / billing</option>
            <option>Other</option>
          </select>
        </div>
        <div>
          <label htmlFor="email">Your email</label>
          <input id="email" name="email" type="email" required placeholder="you@example.com" />
        </div>
        <div>
          <label htmlFor="body">Message</label>
          <textarea
            id="body"
            name="body"
            rows={6}
            required
            placeholder="Describe the issue, include the report id if relevant…"
          />
        </div>
        <button className="primary" type="submit">
          Open email draft
        </button>
      </form>

      <p className="hint">
        Production tip: replace this form with an embedded Tally iframe pointed at your inbox.
      </p>
    </section>
  );
}
