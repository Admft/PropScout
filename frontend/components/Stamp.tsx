type StampVariant = "verdict" | "ready" | "failed";

export default function Stamp({
  text,
  variant,
  size = "md",
  id,
  timestamp,
}: {
  text: string;
  variant: StampVariant;
  size?: "md" | "sm";
  id?: string;
  timestamp?: string;
}) {
  const variantClass = variant === "verdict" ? "stamp-verdict" : variant === "failed" ? "stamp-failed" : "";

  return (
    <span className="stamp-wrap">
      <span className={`stamp stamp-${size} ${variantClass}`}>
        <span className="stamp-word">{text}</span>
        {id && size === "md" && <span className="stamp-id">{id}</span>}
      </span>
      {timestamp && size === "md" && (
        <span className="stamp-meta">
          <span className="lbl">generated</span> {timestamp}
        </span>
      )}
    </span>
  );
}
