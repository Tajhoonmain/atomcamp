import { useState } from "react";
import { motion } from "framer-motion";
import { replaySteps, probabilitySeries } from "../demo";
import { Sparkline } from "./widgets";

export function ReplayPanel() {
  const [active, setActive] = useState(0);
  const [branch, setBranch] = useState(false);
  const step = replaySteps[active];

  return (
    <div className="grid lg:grid-cols-[1.3fr_1fr] gap-4">
      <div className="glass p-5">
        <div className="text-[11px] uppercase tracking-wider text-muted font-semibold mb-4">Replay timeline</div>

        {/* probability ribbon */}
        <div className="mb-5"><Sparkline data={probabilitySeries} height={70} /></div>

        {/* steps */}
        <div className="relative pl-6">
          <div className="absolute left-[7px] top-1 bottom-1 w-px bg-border" />
          {replaySteps.map((s, i) => (
            <button key={s.t} onClick={() => setActive(i)}
              className="relative block text-left w-full py-2 group">
              <motion.span
                className={`absolute -left-[22px] top-3 w-3.5 h-3.5 rounded-full border-2 ${
                  i === active ? "bg-accent border-accent" : s.flag ? "bg-rose-500/80 border-rose-400" : "bg-ink border-primary2"
                }`}
                animate={i === active ? { scale: [1, 1.3, 1] } : {}}
                transition={{ duration: 1.4, repeat: Infinity }}
              />
              <div className="flex items-center gap-2">
                <span className="text-[11px] text-muted font-mono">{s.t}</span>
                <span className={`text-[13px] ${i === active ? "text-white" : "text-[#c7cbda]"} ${s.flag ? "text-rose-300" : ""}`}>{s.label}</span>
                <span className="ml-auto text-[11px] text-accent font-semibold">{Math.round(s.prob * 100)}%</span>
              </div>
            </button>
          ))}
        </div>

        <motion.div key={active} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
          className="mt-4 p-3 rounded-xl border border-border bg-surface2/50 text-[13px] text-[#d7dae6]">
          {step.note}
        </motion.div>
      </div>

      {/* what-if branch */}
      <div className="glass p-5">
        <div className="text-[11px] uppercase tracking-wider text-muted font-semibold mb-4">What-if simulator</div>
        <p className="text-[13px] text-muted leading-relaxed">
          Replay turn <span className="text-white font-mono">{step.t}</span> with a different line and see how the twin
          — and the outcome — would have changed.
        </p>
        <button onClick={() => setBranch((b) => !b)} className="btn-primary px-4 py-2 mt-4 text-sm">
          {branch ? "Reset branch" : "Simulate a stronger line →"}
        </button>

        <div className="mt-6 relative h-44">
          {/* original path */}
          <BranchPath delay={0} color="#6366F1" label="Actual · 78%" y={120} />
          {branch && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <BranchPath delay={0.1} color="#2DD4BF" label="What-if · 86%" y={50} dashed />
              <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}
                className="absolute right-0 top-0 text-[12px] text-accent max-w-[200px] text-right">
                Pricing the case study instead of giving it free lifts the close to ~86%.
              </motion.div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}

function BranchPath({ color, label, y, delay, dashed }: { color: string; label: string; y: number; delay: number; dashed?: boolean }) {
  return (
    <svg className="absolute inset-0 w-full h-full overflow-visible">
      <motion.path
        d={`M10,120 C140,120 160,${y} 320,${y}`}
        fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round"
        strokeDasharray={dashed ? "6 6" : undefined}
        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1, delay }}
      />
      <motion.circle cx="320" cy={y} r="5" fill={color}
        initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: delay + 1 }} />
      <motion.text x="324" y={y + 4} fontSize="12" fill={color} fontFamily="Inter"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: delay + 1 }}>{label}</motion.text>
    </svg>
  );
}
