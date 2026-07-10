import { ImageResponse } from "next/og";

export const alt = "HouseFax — source-cited due diligence for any residential address";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function TwitterImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "64px 72px",
          background: "#1b1917",
          color: "#f3f5f4",
          fontFamily: "Georgia, 'Times New Roman', serif",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            fontSize: 42,
            fontWeight: 700,
            letterSpacing: "-1.5px",
          }}
        >
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: 8,
              background: "#7eb7fe",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#1b1917",
              fontSize: 18,
              fontWeight: 800,
              fontFamily: "ui-monospace, Menlo, monospace",
            }}
          >
            HF
          </div>
          <span>
            House<span style={{ color: "#7eb7fe" }}>Fax</span>
          </span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 18, maxWidth: 900 }}>
          <div
            style={{
              fontSize: 64,
              fontWeight: 700,
              letterSpacing: "-1.8px",
              lineHeight: 1.05,
            }}
          >
            Know the house before you buy it.
          </div>
          <div
            style={{
              fontSize: 26,
              color: "rgba(243,245,244,0.72)",
              lineHeight: 1.35,
              maxWidth: 720,
            }}
          >
            Source-cited due diligence. Tools calculate. The model explains.
          </div>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-end",
            fontFamily: "ui-monospace, Menlo, monospace",
            fontSize: 16,
            color: "rgba(243,245,244,0.5)",
            letterSpacing: "0.04em",
          }}
        >
          <span>DECISION SUPPORT · NOT ADVICE</span>
          <span style={{ color: "#7eb7fe" }}>housefax.ai</span>
        </div>
      </div>
    ),
    { ...size }
  );
}
