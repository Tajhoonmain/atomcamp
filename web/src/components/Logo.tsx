// Mirror Mark — two mirrored uprights + a teal leverage diagonal forming an N.
export function Mark({ size = 36 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none" aria-label="Negotiation Digital Twin">
      <rect x="20" y="14" width="16" height="72" rx="8" fill="currentColor" />
      <rect x="64" y="14" width="16" height="72" rx="8" fill="currentColor" />
      <line x1="28" y1="22" x2="72" y2="78" stroke="#2DD4BF" strokeWidth="15" strokeLinecap="round" />
    </svg>
  );
}

export function Wordmark({ size = 34 }: { size?: number }) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-white">
        <Mark size={size} />
      </span>
      <div className="leading-tight">
        <div className="font-sora font-semibold text-[15px] text-white tracking-tight">Negotiation</div>
        <div className="font-sora text-[15px] text-muted -mt-0.5">Digital Twin</div>
      </div>
    </div>
  );
}
