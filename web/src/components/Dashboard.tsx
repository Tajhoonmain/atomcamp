import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  persona, transcript, coachByUserTurn, suggestedMove, probabilitySeries,
  leverage, persuasion, agents, retrievalFeed, outcome,
} from "../demo";
import { AnimatedNumber, Gauge, Sparkline, AgentChip } from "./widgets";
import { KnowledgeGraph } from "./KnowledgeGraph";
import { ReplayPanel } from "./Replay";
import { Mark } from "./Logo";

const pillStyle: Record<string, React.CSSProperties> = {
  leverage: { background: "rgba(45,212,191,0.14)", color: "#2DD4BF" },
  mistake: { background: "rgba(239,68,68,0.14)", color: "#F87171" },
  tactic: { background: "rgba(79,70,229,0.18)", color: "#A5B4FC" },
  tip: { background: "rgba(138,144,166,0.16)", color: "#C7CBDA" },
};

export function Dashboard({ onExit }: { onExit: () => void }) {
  const [revealed, setRevealed] = useState(0); // fully shown turns
  const [typing, setTyping] = useState<string | null>(null);
  const [playing, setPlaying] = useState(true);
  const [tab, setTab] = useState<"command" | "replay">("command");
  const scroller = useRef<HTMLDivElement>(null);

  // playback loop
  useEffect(() => {
    if (!playing || revealed >= transcript.length) return;
    const turn = transcript[revealed];
    let cancelled = false;
    if (turn.speaker === "user") {
      const id = setTimeout(() => !cancelled && setRevealed((r) => r + 1), 850);
      return () => { cancelled = true; clearTimeout(id); };
    }
    // twin: stream characters
    let i = 0;
    setTyping("");
    const id = setInterval(() => {
      i += 3;
      setTyping(turn.text.slice(0, i));
      if (i >= turn.text.length) {
        clearInterval(id);
        setTimeout(() => { if (!cancelled) { setTyping(null); setRevealed((r) => r + 1); } }, 500);
      }
    }, 16);
    return () => { cancelled = true; clearInterval(id); };
  }, [revealed, playing]);

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: "smooth" });
  }, [revealed, typing]);

  const shown = transcript.slice(0, revealed);
  const userTurnsShown = shown.filter((t) => t.speaker === "user").length;
  const probIdx = Math.max(0, Math.min(revealed, probabilitySeries.length) - 1);
  const prob = probabilitySeries[probIdx] ?? probabilitySeries[0];
  const insights = coachByUserTurn[userTurnsShown - 1] ?? [];
  const done = revealed >= transcript.length;
  const twinSpeaking = typing !== null;

  return (
    <div className="min-h-screen flex flex-col">
      {/* header */}
      <header className="h-14 border-b border-border/70 bg-ink/70 backdrop-blur flex items-center px-5 gap-4 sticky top-0 z-30">
        <span className="text-white"><Mark size={24} /></span>
        <div className="text-sm font-medium">SaaS renewal · vs Dana Whitlock</div>
        <span className="pill" style={{ background: "rgba(45,212,191,0.14)", color: "#2DD4BF" }}>
          <span className="w-1.5 h-1.5 rounded-full bg-accent blink" /> LIVE
        </span>
        <div className="ml-auto flex items-center gap-2">
          <div className="flex rounded-lg border border-border overflow-hidden text-xs">
            {(["command", "replay"] as const).map((t) => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-3 py-1.5 capitalize ${tab === t ? "bg-primary text-white" : "text-muted hover:text-white"}`}>
                {t === "command" ? "Command center" : "Replay"}
              </button>
            ))}
          </div>
          <button onClick={() => { setRevealed(0); setTyping(null); setPlaying(true); }}
            className="btn-ghost px-3 py-1.5 text-xs">↻ Restart</button>
          <button onClick={onExit} className="btn-ghost px-3 py-1.5 text-xs">Exit</button>
        </div>
      </header>

      {tab === "replay" ? (
        <div className="p-5"><ReplayPanel /></div>
      ) : (
        <div className="flex-1 grid grid-cols-12 gap-4 p-4">
          {/* LEFT */}
          <div className="col-span-12 lg:col-span-3 space-y-4">
            <Panel title="Digital Twin">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-full grid place-items-center font-sora font-semibold text-sm"
                  style={{ background: "rgba(99,102,241,0.2)", color: "#A5B4FC" }}>{persona.avatar}</div>
                <div>
                  <div className="font-medium text-sm">{persona.name}</div>
                  <div className="text-[11px] text-muted">{persona.role}</div>
                </div>
                {twinSpeaking && <span className="ml-auto pill" style={pillStyle.tactic}>speaking</span>}
              </div>
              <p className="text-[12px] text-muted mt-3 leading-relaxed">{persona.style}</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {persona.tactics.map((t) => (
                  <span key={t} className="text-[10px] px-2 py-0.5 rounded-md border border-border text-muted">{t}</span>
                ))}
              </div>
            </Panel>

            <Panel title="Active Agents">
              {agents.map((a) => (
                <AgentChip key={a.name} name={a.name} desc={a.desc}
                  state={a.name === "Twin" && twinSpeaking ? "speaking" : a.state} />
              ))}
            </Panel>

            <Panel title="Retrieval activity">
              <div className="space-y-1.5">
                {retrievalFeed.map((r, i) => (
                  <motion.div key={r} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6 + i * 0.5 }}
                    className="text-[11px] text-muted flex items-center gap-2">
                    <span className="text-accent">›</span>{r}
                  </motion.div>
                ))}
              </div>
            </Panel>
          </div>

          {/* CENTER */}
          <div className="col-span-12 lg:col-span-6 space-y-4">
            <Panel title="Live transcript" className="flex flex-col" style={{ height: 460 }}>
              <div ref={scroller} className="flex-1 overflow-y-auto pr-2 space-y-3">
                <AnimatePresence>
                  {shown.map((t, i) => <Bubble key={i} turn={t} />)}
                </AnimatePresence>
                {twinSpeaking && (
                  <Bubble turn={{ speaker: "twin", text: typing!, t: "" }} streaming />
                )}
                {done && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    className="text-center text-[11px] text-muted py-2">— rehearsal complete —</motion.div>
                )}
              </div>
            </Panel>

            <Panel title="Coach">
              <AnimatePresence mode="popLayout">
                {insights.map((ins, i) => (
                  <motion.div key={ins.text} layout
                    initial={{ opacity: 0, y: 10, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ delay: i * 0.1 }}
                    className="flex items-start gap-2.5 py-1.5">
                    <span className="pill mt-0.5" style={pillStyle[ins.kind]}>{ins.kind}</span>
                    <span className="text-[13px] text-[#d7dae6] leading-snug">{ins.text}</span>
                  </motion.div>
                ))}
              </AnimatePresence>
              {done && (
                <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                  className="mt-3 p-3 rounded-xl border border-accent/40" style={{ background: "rgba(45,212,191,0.08)" }}>
                  <div className="pill mb-1.5" style={pillStyle.leverage}>recommended close</div>
                  <p className="text-[13px] text-[#d7dae6] leading-relaxed">{suggestedMove}</p>
                </motion.div>
              )}
            </Panel>
          </div>

          {/* RIGHT */}
          <div className="col-span-12 lg:col-span-3 space-y-4">
            <Panel title="Outcome prediction">
              <div className="flex items-end gap-2">
                <div className="font-sora font-semibold text-4xl text-accent">
                  <AnimatedNumber value={prob * 100} decimals={0} suffix="%" />
                </div>
                <div className="text-[11px] text-muted mb-1.5">deal probability</div>
              </div>
              <div className="mt-1"><Sparkline data={probabilitySeries.slice(0, Math.max(2, revealed))} /></div>
              <div className="mt-2 flex items-center justify-between text-[11px]">
                <span className="text-muted">Favorability to you</span>
                <span className="font-semibold text-[#d7dae6]">{Math.round(outcome.favorability * 100)}%</span>
              </div>
            </Panel>

            <Panel title="Persuasion analytics">
              <div className="grid grid-cols-2 gap-3">
                {persuasion.map((p) => <Gauge key={p.label} value={p.value} label={p.label} delta={p.delta} />)}
              </div>
            </Panel>

            <Panel title="Leverage opportunities">
              <div className="space-y-2.5">
                {leverage.map((l, i) => (
                  <div key={l.label}>
                    <div className="flex justify-between text-[11px] mb-1">
                      <span className="text-[#d7dae6]">{l.label}</span>
                      <span className="text-muted">{Math.round(l.strength * 100)}</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-surface2 overflow-hidden">
                      <motion.div className="h-full rounded-full"
                        style={{ background: "linear-gradient(90deg,#4F46E5,#2DD4BF)" }}
                        initial={{ width: 0 }} animate={{ width: `${l.strength * 100}%` }}
                        transition={{ duration: 1, delay: 0.3 + i * 0.12 }} />
                    </div>
                  </div>
                ))}
              </div>
            </Panel>
          </div>

          {/* KNOWLEDGE GRAPH */}
          <div className="col-span-12">
            <Panel title="Knowledge graph · live relationship map">
              <div style={{ height: 300 }}><KnowledgeGraph /></div>
            </Panel>
          </div>
        </div>
      )}
    </div>
  );
}

function Panel({ title, children, className = "", style }: {
  title: string; children: React.ReactNode; className?: string; style?: React.CSSProperties;
}) {
  return (
    <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
      className={`glass glass-hover p-4 ${className}`} style={style}>
      <div className="text-[11px] uppercase tracking-wider text-muted font-semibold mb-3">{title}</div>
      {children}
    </motion.div>
  );
}

function Bubble({ turn, streaming }: { turn: { speaker: string; text: string; t: string; tactic?: string }; streaming?: boolean }) {
  const isUser = turn.speaker === "user";
  return (
    <motion.div layout initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[82%] rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed ${
        isUser ? "bg-primary/20 border border-primary/30" : "bg-surface2/70 border border-border"
      }`}>
        {!isUser && (
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-semibold text-[#A5B4FC]">{persona.name}</span>
            {turn.tactic && <span className="text-[10px] px-1.5 py-0.5 rounded text-accent" style={{ background: "rgba(45,212,191,0.1)" }}>{turn.tactic}</span>}
          </div>
        )}
        <span className="text-[#e6e8f0]">{turn.text}</span>
        {streaming && <span className="inline-block w-1.5 h-3.5 bg-accent ml-0.5 align-middle blink" />}
      </div>
    </motion.div>
  );
}
