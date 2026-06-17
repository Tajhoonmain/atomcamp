import { useRef, useState } from "react";
import { motion } from "framer-motion";
import { apiBase } from "../api";
import { persona } from "../demo";
import { Mark } from "./Logo";

type Line = { who: "you" | "twin" | "sys"; text: string };

// Live voice agent. Backend mints an ephemeral token; the browser does WebRTC
// straight to OpenAI. Your real key never reaches this component.
export function VoiceAgent({ onClose }: { onClose: () => void }) {
  const [status, setStatus] = useState("idle");
  const [live, setLive] = useState(false);
  const [log, setLog] = useState<Line[]>([]);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const micRef = useRef<MediaStream | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const twinBuf = useRef("");

  const push = (line: Line) => setLog((l) => [...l, line]);

  function onEvent(data: string) {
    let m: { type?: string; delta?: string; transcript?: string; error?: { message?: string } };
    try {
      m = JSON.parse(data);
    } catch {
      return;
    }
    const t = m.type ?? "";
    if (t.endsWith("transcript.delta")) {
      twinBuf.current += m.delta ?? "";
    } else if (t.endsWith("transcript.done") || t === "response.done") {
      if (twinBuf.current.trim()) push({ who: "twin", text: twinBuf.current.trim() });
      twinBuf.current = "";
    } else if (t === "conversation.item.input_audio_transcription.completed") {
      if (m.transcript?.trim()) push({ who: "you", text: m.transcript.trim() });
    } else if (t === "error") {
      push({ who: "sys", text: m.error?.message ?? "error" });
    }
  }

  async function start() {
    const base = apiBase();
    if (!base) {
      setStatus("error");
      push({ who: "sys", text: "Voice needs the backend. Set VITE_API_BASE_URL to your ndt-api URL." });
      return;
    }
    setStatus("minting token…");
    try {
      const r = await fetch(`${base}/realtime/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      if (!r.ok) throw new Error(`/realtime/session ${r.status}: ${await r.text()}`);
      const sess = await r.json();
      const ek: string | undefined = sess.value;
      if (!ek) throw new Error("no ephemeral token returned");

      setStatus("getting mic…");
      const mic = await navigator.mediaDevices.getUserMedia({ audio: true });
      micRef.current = mic;

      const pc = new RTCPeerConnection();
      pcRef.current = pc;
      pc.ontrack = (e: RTCTrackEvent) => {
        if (audioRef.current) audioRef.current.srcObject = e.streams[0];
      };
      mic.getTracks().forEach((tr) => pc.addTrack(tr, mic));
      const dc = pc.createDataChannel("oai-events");
      dc.onmessage = (e: MessageEvent) => onEvent(e.data as string);

      setStatus("connecting to OpenAI…");
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      const resp = await fetch("https://api.openai.com/v1/realtime/calls", {
        method: "POST",
        body: offer.sdp ?? "",
        headers: { Authorization: `Bearer ${ek}`, "Content-Type": "application/sdp" },
      });
      if (!resp.ok) throw new Error(`OpenAI calls ${resp.status}: ${await resp.text()}`);
      await pc.setRemoteDescription({ type: "answer", sdp: await resp.text() });

      setLive(true);
      setStatus("🟢 live — start speaking");
      push({ who: "sys", text: "Connected. Open with your first line." });
    } catch (err) {
      setStatus("error");
      push({ who: "sys", text: err instanceof Error ? err.message : String(err) });
    }
  }

  function stop() {
    micRef.current?.getTracks().forEach((t) => t.stop());
    pcRef.current?.close();
    setLive(false);
    setStatus("ended");
  }

  function close() {
    stop();
    onClose();
  }

  const color: Record<Line["who"], string> = { you: "#A5B4FC", twin: "#2DD4BF", sys: "#8A90A6" };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(5,8,16,0.7)",
        backdropFilter: "blur(6px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 50,
      }}
      onClick={close}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className="glass"
        style={{ width: "min(560px, 92vw)", padding: 24 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 mb-4">
          <span className="text-white"><Mark size={26} /></span>
          <div className="flex-1">
            <div className="font-sora font-medium text-[15px]">Voice negotiation · {persona.name}</div>
            <div className="text-[11px] text-muted">Live spoken rehearsal — your key stays on the server</div>
          </div>
          <span className="pill" style={{ background: "rgba(45,212,191,0.14)", color: "#2DD4BF" }}>{status}</span>
        </div>

        <div className="flex gap-3 mb-4">
          {!live ? (
            <button onClick={start} className="btn-primary px-5 py-2.5 text-sm">🎙️ Start talking</button>
          ) : (
            <button onClick={stop} className="btn-ghost px-5 py-2.5 text-sm" style={{ borderColor: "rgba(239,68,68,0.5)", color: "#F87171" }}>End</button>
          )}
          <button onClick={close} className="btn-ghost px-5 py-2.5 text-sm">Close</button>
        </div>

        <div
          style={{
            background: "rgba(10,14,26,0.6)",
            border: "1px solid #222842",
            borderRadius: 12,
            padding: 14,
            height: 240,
            overflowY: "auto",
            fontSize: 13,
            lineHeight: 1.55,
          }}
        >
          {log.length === 0 ? (
            <span className="text-muted text-[12px]">Transcript will appear here as you talk.</span>
          ) : (
            log.map((l, i) => (
              <div key={i} style={{ color: color[l.who] }}>
                {l.who === "you" ? "You: " : l.who === "twin" ? `${persona.name}: ` : ""}
                {l.text}
              </div>
            ))
          )}
        </div>

        <audio ref={audioRef} autoPlay />
      </motion.div>
    </div>
  );
}
