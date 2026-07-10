"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

type DocRow = {
  id: string;
  name: string;
  doc_type: "inspection" | "disclosure" | "hoa" | "other";
  status: "Queued" | "Processing" | "Ready" | "Failed";
  flags: string[];
};

export default function ReportDocumentsPage() {
  const params = useParams();
  const addressId = decodeURIComponent(String(params.address_id ?? ""));
  const [docs, setDocs] = useState<DocRow[]>([
    {
      id: "d1",
      name: "inspection-report.pdf",
      doc_type: "inspection",
      status: "Ready",
      flags: ["Roof near end of life noted on p.12", "Active drip under kitchen sink (p.18)"],
    },
  ]);
  const [uploading, setUploading] = useState(false);

  function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const id = `d${Date.now()}`;
    setDocs((prev) => [
      {
        id,
        name: file.name,
        doc_type: "other",
        status: "Processing",
        flags: [],
      },
      ...prev,
    ]);
    // Demo: simulate LlamaIndex processing
    setTimeout(() => {
      setDocs((prev) =>
        prev.map((d) =>
          d.id === id
            ? {
                ...d,
                status: "Ready",
                flags: ["Document indexed — findings will appear on the report when RAG is live."],
              }
            : d
        )
      );
      setUploading(false);
    }, 1800);
  }

  return (
    <section className="page-card">
      <div className="page-header">
        <div>
          <h1>Property documents</h1>
          <p className="sub">
            Upload inspection reports, disclosures, and HOA docs for this property. They feed the
            LlamaIndex document-intelligence module and surface red flags on the report.
          </p>
        </div>
        <Link href={`/report/${encodeURIComponent(addressId)}`}>← Back to report</Link>
      </div>

      <label className="upload-box">
        <input type="file" accept=".pdf,.png,.jpg,.jpeg,.txt" onChange={onUpload} hidden />
        <span>{uploading ? "Uploading…" : "Choose file to upload"}</span>
      </label>

      <div className="doc-list">
        {docs.map((d) => (
          <article key={d.id} className="doc-row">
            <div>
              <strong>{d.name}</strong>
              <p className="muted-sm">
                {d.doc_type} · <span className="ledger-tag">{d.status}</span>
              </p>
            </div>
            {d.flags.length > 0 && (
              <ul className="questions">
                {d.flags.map((f) => (
                  <li key={f}>{f}</li>
                ))}
              </ul>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
