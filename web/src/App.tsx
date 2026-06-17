import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Landing } from "./components/Landing";
import { Dashboard } from "./components/Dashboard";

type View = "landing" | "loading" | "demo";

export default function App() {
  const [view, setView] = useState<View>("landing");

  // Judge Mode: one click → a brief "spinning up" beat → live demo.
  const launch = () => {
    setView("loading");
    setTimeout(() => setView("demo"), 1400);
  };

  return (
    <AnimatePresence mode="wait">
      {view === "landing" && (
        <motion.div key="landing" exit={{ opacity: 0 }}>
          <Landing onLaunch={launch} />
        </motion.div>
      )}
      {view === "loading" && <LaunchSplash key="loading" />}
      {view === "demo" && (
        <motion.div key="demo" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
          <Dashboard onExit={() => setView("landing")} />
        </motion.div>
      )}
    </AnimatePresence>
  );
}

const steps = ["Generating digital twin", "Loading negotiation scenario", "Spinning up coach + predictor", "Connecting knowledge graph"];

function LaunchSplash() {
  return (
    <motion.div key="splash" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="min-h-screen grid place-items-center relative overflow-hidden">
      <div className="aurora animate-drift" style={{ width: 420, height: 420, background: "#4F46E5", top: "20%", left: "30%" }} />
      <div className="relative text-center">
        <motion.div
          className="mx-auto w-16 h-16 rounded-2xl grid place-items-center mb-6"
          style={{ background: "#0A0E1A", border: "1px solid #222842" }}
          animate={{ boxShadow: ["0 0 0 rgba(45,212,191,0)", "0 0 30px rgba(45,212,191,0.5)", "0 0 0 rgba(45,212,191,0)"] }}
          transition={{ duration: 1.6, repeat: Infinity }}
        >
          <svg width="40" height="40" viewBox="0 0 100 100">
            <rect x="20" y="14" width="16" height="72" rx="8" fill="#fff" />
            <rect x="64" y="14" width="16" height="72" rx="8" fill="#fff" />
            <line x1="28" y1="22" x2="72" y2="78" stroke="#2DD4BF" strokeWidth="15" strokeLinecap="round" />
          </svg>
        </motion.div>
        <div className="space-y-1.5">
          {steps.map((s, i) => (
            <motion.div key={s} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.3 }} className="text-sm text-muted flex items-center gap-2 justify-center">
              <span className="text-accent">✓</span> {s}
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
