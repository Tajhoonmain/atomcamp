import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

// Counts up to `value` with easing — used for the probability headline.
export function AnimatedNumber({ value, suffix = "", decimals = 0, duration = 1200 }: {
  value: number; suffix?: string; decimals?: number; duration?: number;
}) {
  const [n, setN] = useState(0);
  const from = useRef(0);
  useEffect(() => {
    const start = performance.now();
    const a = from.current;
    let raf = 0;
    const tick = (now: number) => {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setN(a + (value - a) * eased);
      if (p < 1) raf = requestAnimationFrame(tick);
      else from.current = value;
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value, duration]);
  return <span>{n.toFixed(decimals)}{suffix}</span>;
}

// Radial gauge for persuasion metrics.
export function Gauge({ value, label, delta }: { value: number; label: string; delta?: number }) {
  const r = 30;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(1, value));
  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative" style={{ width: 76, height: 76 }}>
        <svg width="76" height="76" className="-rotate-90">
          <circle cx="38" cy="38" r={r} fill="none" stroke="#222842" strokeWidth="7" />
          <motion.circle
            cx="38" cy="38" r={r} fill="none" stroke="#2DD4BF" strokeWidth="7" strokeLinecap="round"
            strokeDasharray={c}
            initial={{ strokeDashoffset: c }}
            animate={{ strokeDashoffset: c * (1 - pct) }}
            transition={{ duration: 1.1, ease: "easeOut" }}
          />
        </svg>
        <div className="absolute inset-0 grid place-items-center font-sora text-sm font-semibold">
          {Math.round(pct * 100)}
        </div>
      </div>
      <div className="text-[11px] text-muted text-center leading-tight">{label}</div>
      {delta !== undefined && (
        <div className={`text-[10px] font-semibold ${delta >= 0 ? "text-accent" : "text-rose-400"}`}>
          {delta >= 0 ? "▲" : "▼"} {Math.abs(Math.round(delta * 100))}
        </div>
      )}
    </div>
  );
}

// Sparkline that draws itself in.
export function Sparkline({ data, height = 60 }: { data: number[]; height?: number }) {
  const w = 280;
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const pts = data.map((d, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = height - ((d - min) / (max - min || 1)) * (height - 8) - 4;
    return [x, y] as const;
  });
  const path = pts.map((p, i) => (i === 0 ? `M${p[0]},${p[1]}` : `L${p[0]},${p[1]}`)).join(" ");
  const area = `${path} L${w},${height} L0,${height} Z`;
  return (
    <svg width="100%" viewBox={`0 0 ${w} ${height}`} preserveAspectRatio="none" className="overflow-visible">
      <defs>
        <linearGradient id="spark" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(45,212,191,0.30)" />
          <stop offset="100%" stopColor="rgba(45,212,191,0)" />
        </linearGradient>
      </defs>
      <motion.path d={area} fill="url(#spark)"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1, delay: 0.5 }} />
      <motion.path d={path} fill="none" stroke="#2DD4BF" strokeWidth="2.5" strokeLinecap="round"
        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.4, ease: "easeInOut" }} />
      {pts.map((p, i) => (
        <motion.circle key={i} cx={p[0]} cy={p[1]} r="3" fill="#6366F1"
          initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.4 + i * 0.12 }} />
      ))}
    </svg>
  );
}

const stateStyle: Record<string, string> = {
  speaking: "text-accent",
  thinking: "text-primary2",
  done: "text-muted",
};

export function AgentChip({ name, desc, state }: { name: string; desc: string; state: string }) {
  return (
    <div className="flex items-center gap-3 py-2">
      <div className={`relative w-2.5 h-2.5 rounded-full ${state === "done" ? "bg-muted" : "bg-accent"} ${state !== "done" ? "pulse-ring" : ""}`} />
      <div className="flex-1 min-w-0">
        <div className="text-[13px] font-medium flex items-center gap-2">
          {name}
          <span className={`text-[10px] uppercase tracking-wide ${stateStyle[state]}`}>
            {state === "thinking" ? (
              <span className="inline-flex gap-0.5">
                thinking
                <span className="dot">.</span><span className="dot" style={{ animationDelay: "0.2s" }}>.</span><span className="dot" style={{ animationDelay: "0.4s" }}>.</span>
              </span>
            ) : state}
          </span>
        </div>
        <div className="text-[11px] text-muted truncate">{desc}</div>
      </div>
    </div>
  );
}
