import { useState } from "react";
import { motion } from "framer-motion";
import { graph } from "../demo";

const W = 440;
const H = 300;

const nodeColor: Record<string, string> = {
  self: "#2DD4BF",
  twin: "#6366F1",
  lever: "#4F46E5",
  trade: "#8A90A6",
};

export function KnowledgeGraph() {
  const [hover, setHover] = useState<string | null>(null);
  const pos = (id: string) => {
    const n = graph.nodes.find((x) => x.id === id)!;
    return { x: n.x * W, y: n.y * H };
  };

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-full">
      {/* edges grow in */}
      {graph.edges.map((e, i) => {
        const a = pos(e.from);
        const b = pos(e.to);
        const active = hover === e.from || hover === e.to;
        return (
          <motion.line
            key={i}
            x1={a.x} y1={a.y} x2={b.x} y2={b.y}
            stroke={active ? "#2DD4BF" : "rgba(99,102,241,0.4)"}
            strokeWidth={active ? 2 : 1.2}
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ duration: 0.7, delay: 0.3 + i * 0.12 }}
          />
        );
      })}

      {/* nodes spring in */}
      {graph.nodes.map((n, i) => {
        const p = pos(n.id);
        const color = nodeColor[n.kind] || "#6366F1";
        const isHub = n.kind === "self" || n.kind === "twin";
        return (
          <motion.g
            key={n.id}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: "spring", stiffness: 220, damping: 16, delay: 0.2 + i * 0.1 }}
            style={{ transformOrigin: `${p.x}px ${p.y}px`, cursor: "pointer" }}
            onMouseEnter={() => setHover(n.id)}
            onMouseLeave={() => setHover(null)}
          >
            {isHub && (
              <motion.circle
                cx={p.x} cy={p.y} r={16} fill="none" stroke={color} strokeWidth="1.5"
                animate={{ r: [16, 26, 16], opacity: [0.6, 0, 0.6] }}
                transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
              />
            )}
            <circle cx={p.x} cy={p.y} r={hover === n.id ? 11 : isHub ? 9 : 6.5} fill={color}
              style={{ filter: `drop-shadow(0 0 6px ${color})`, transition: "r .15s ease" }} />
            <text x={p.x} y={p.y - 14} textAnchor="middle" fontSize="11"
              fill={hover === n.id ? "#fff" : "#c7cbda"} fontFamily="Inter">
              {n.label}
            </text>
          </motion.g>
        );
      })}
    </svg>
  );
}
