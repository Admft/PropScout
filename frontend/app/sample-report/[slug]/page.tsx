import ReportView from "@/components/ReportView";
import { SAMPLE_REPORT } from "@/lib/sample-report";
import Link from "next/link";

export default function SampleReportPage() {
  return (
    <>
      <div className="sample-banner no-print">
        <strong>Sample report</strong> — static JSON, $0 in API calls.{" "}
        <Link href="/search">Run a live analysis →</Link>
      </div>
      <ReportView report={SAMPLE_REPORT} />
    </>
  );
}
