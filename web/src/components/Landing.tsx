import { motion } from "framer-motion";
import { ParticleField } from "./ParticleField";
import { Mark, Wordmark } from "./Logo";

const fade = {
  hidden: { opacity: 0, y: 24 },
  show: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.6, ease: [0.21, 0.6, 0.35, 1] },
  }),
};

function Reveal({ children, i = 0, className = "" }: { children: React.ReactNode; i?: number; className?: string }) {
  return (
    <motion.div
      variants={fade}
      custom={i}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.3 }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export function Landing({ onLaunch }: { onLaunch: () => void }) {
  return (
    <div className="relative">
      {/* top nav */}
      <nav className="fixed top-0 inset-x-0 z-40 backdrop-blur-md bg-ink/60 border-b border-border/60">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Wordmark size={30} />
          <div className="hidden md:flex items-center gap-8 text-sm text-muted">
            <a className="hover:text-white transition" href="#problem">Problem</a>
            <a className="hover:text-white transition" href="#solution">Solution</a>
            <a className="hover:text-white transition" href="#features">Features</a>
          </div>
          <button onClick={onLaunch} className="btn-primary px-4 py-2 text-sm">Launch Demo</button>
        </div>
      </nav>

      {/* HERO */}
      <section className="relative min-h-screen flex items-center overflow-hidden">
        <div className="aurora animate-drift" style={{ width: 520, height: 520, background: "#4F46E5", top: -120, left: -80 }} />
        <div className="aurora animate-drift" style={{ width: 480, height: 480, background: "#2DD4BF", bottom: -160, right: -60, animationDelay: "3s" }} />
        <ParticleField className="opacity-70" />
        <div className="relative max-w-6xl mx-auto px-6 pt-24 grid lg:grid-cols-[1.1fr_0.9fr] gap-12 items-center">
          <div>
            <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
              className="pill mb-6" style={{ background: "rgba(45,212,191,0.12)", color: "#2DD4BF" }}>
              <span className="w-1.5 h-1.5 rounded-full bg-accent blink" /> Enterprise AI · Negotiation Intelligence
            </motion.div>
            <motion.h1
              initial={{ opacity: 0, y: 22 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.05 }}
              className="font-sora font-semibold text-5xl md:text-6xl leading-[1.05]">
              <span className="text-gradient">Win the conversation</span><br /> before it happens.
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.18 }}
              className="mt-6 text-lg text-muted max-w-xl leading-relaxed">
              Build an AI-powered digital twin of your counterparty and practice high-stakes
              negotiations — with a live coach and outcome prediction — before the real meeting.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.3 }}
              className="mt-9 flex flex-wrap gap-4">
              <button onClick={onLaunch} className="btn-primary px-7 py-3.5 text-[15px]">Launch Demo →</button>
              <button onClick={onLaunch} className="btn-ghost px-7 py-3.5 text-[15px]">Watch the 90s demo</button>
            </motion.div>
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1, delay: 0.5 }}
              className="mt-10 flex items-center gap-6 text-xs text-muted">
              <span>No setup · one click</span>
              <span className="h-3 w-px bg-border" />
              <span>Live coaching</span>
              <span className="h-3 w-px bg-border" />
              <span>Outcome prediction</span>
            </motion.div>
          </div>

          {/* twin visualization */}
          <motion.div
            initial={{ opacity: 0, scale: 0.92 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.8, delay: 0.2 }}
            className="relative">
            <TwinOrb />
          </motion.div>
        </div>
        <div className="absolute bottom-6 inset-x-0 text-center text-muted text-xs">scroll to explore ↓</div>
      </section>

      {/* PROBLEM */}
      <Section id="problem" eyebrow="The problem" title="High-stakes negotiations are won or lost before the meeting.">
        <div className="grid md:grid-cols-3 gap-5 mt-10">
          {[
            ["You can't rehearse", "Real practice means burning a real counterparty. There's no flight simulator for a negotiation."],
            ["You can't read leverage live", "By the time you spot the tell, the moment's gone. Leverage is invisible in the moment."],
            ["You walk in blind", "No model of how they'll anchor, where they'll bend, or what they actually need."],
          ].map(([h, p], i) => (
            <Reveal i={i} key={h}>
              <div className="glass glass-hover p-6 h-full">
                <div className="text-accent text-sm font-semibold mb-2">0{i + 1}</div>
                <h3 className="font-sora text-lg mb-2">{h}</h3>
                <p className="text-muted text-sm leading-relaxed">{p}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </Section>

      {/* SOLUTION */}
      <Section id="solution" eyebrow="The solution" title="Rehearse against a digital twin of the other side.">
        <div className="grid md:grid-cols-2 gap-5 mt-10">
          {[
            ["Digital Twin", "Generate a psychologically-grounded model of your counterparty — goals, BATNA, tactics, and a hidden bottom line it protects."],
            ["Live Coach", "Every move is scored in real time: leverage you're missing, mistakes you just made, and the single best next line."],
            ["Outcome Prediction", "A calibrated probability the deal closes — and how favorable — recomputed turn by turn."],
            ["Replay & What-If", "Rewind the conversation, find the turning points, and replay a different line to see how it would have gone."],
          ].map(([h, p], i) => (
            <Reveal i={i} key={h}>
              <div className="glass glass-hover p-6 flex gap-4">
                <div className="text-accent shrink-0"><Mark size={26} /></div>
                <div>
                  <h3 className="font-sora text-lg mb-1.5">{h}</h3>
                  <p className="text-muted text-sm leading-relaxed">{p}</p>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </Section>

      {/* ARCHITECTURE */}
      <Section id="architecture" eyebrow="Architecture" title="Five agents, one live loop.">
        <Reveal>
          <div className="glass p-8 mt-8">
            <div className="flex flex-wrap items-center justify-center gap-3 text-sm">
              {["Voice in", "Twin (persona + RAG)", "Coach", "Predictor", "Replay"].map((s, i) => (
                <div key={s} className="flex items-center gap-3">
                  <span className="px-4 py-2 rounded-xl border border-border bg-surface2/60">{s}</span>
                  {i < 4 && <span className="text-primary2">→</span>}
                </div>
              ))}
            </div>
            <p className="text-center text-muted text-sm mt-6">
              Each turn: transcribe → twin responds in character → coach + predictor analyze concurrently → persist → speak.
            </p>
          </div>
        </Reveal>
      </Section>

      {/* FEATURES */}
      <Section id="features" eyebrow="Features" title="A command center for the conversation.">
        <div className="grid md:grid-cols-4 gap-4 mt-10">
          {["Digital Twin", "Live Transcript", "Coach Insights", "Active Agents", "Outcome Prediction", "Leverage Map", "Knowledge Graph", "Persuasion Analytics"].map((f, i) => (
            <Reveal i={i % 4} key={f}>
              <div className="glass glass-hover p-5 text-sm font-medium">{f}</div>
            </Reveal>
          ))}
        </div>
      </Section>

      {/* CTA */}
      <section className="relative py-28 overflow-hidden">
        <div className="aurora animate-drift" style={{ width: 480, height: 480, background: "#4F46E5", left: "50%", top: "10%", transform: "translateX(-50%)" }} />
        <Reveal>
          <div className="relative max-w-3xl mx-auto px-6 text-center">
            <h2 className="font-sora font-semibold text-4xl md:text-5xl">Negotiate with the upside <span className="text-gradient">already in your corner.</span></h2>
            <p className="text-muted mt-5">Train against your twin. Then win the real one.</p>
            <button onClick={onLaunch} className="btn-primary px-8 py-4 mt-9 text-base">Launch the live demo →</button>
          </div>
        </Reveal>
      </section>

      <footer className="border-t border-border/60 py-8 text-center text-muted text-xs">
        Negotiation Digital Twin · built for the demo · Mirror Mark identity
      </footer>
    </div>
  );
}

function Section({ id, eyebrow, title, children }: { id?: string; eyebrow: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="max-w-6xl mx-auto px-6 py-24">
      <Reveal>
        <div className="text-accent text-sm font-semibold tracking-wide uppercase">{eyebrow}</div>
        <h2 className="font-sora font-semibold text-3xl md:text-4xl mt-3 max-w-2xl">{title}</h2>
      </Reveal>
      {children}
    </section>
  );
}

// Animated "digital twin" orb — two mirrored arcs orbiting a core.
function TwinOrb() {
  return (
    <div className="relative aspect-square max-w-md mx-auto">
      <div className="absolute inset-0 rounded-full" style={{ background: "radial-gradient(circle at 50% 50%, rgba(79,70,229,0.25), transparent 60%)" }} />
      {[0, 1, 2].map((r) => (
        <motion.div
          key={r}
          className="absolute rounded-full border"
          style={{
            inset: 30 + r * 38,
            borderColor: r === 1 ? "rgba(45,212,191,0.5)" : "rgba(99,102,241,0.35)",
          }}
          animate={{ rotate: r % 2 ? -360 : 360 }}
          transition={{ duration: 22 + r * 8, repeat: Infinity, ease: "linear" }}
        >
          <span
            className="absolute w-2.5 h-2.5 rounded-full"
            style={{ background: r === 1 ? "#2DD4BF" : "#6366F1", top: -5, left: "50%", boxShadow: "0 0 12px currentColor" }}
          />
        </motion.div>
      ))}
      <div className="absolute inset-0 grid place-items-center">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="text-white"
        >
          <Mark size={84} />
        </motion.div>
      </div>
    </div>
  );
}
