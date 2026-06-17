// Scripted, realistic negotiation used by Judge Mode. No backend / API key
// needed — this is what guarantees the demo "wows" within 15 seconds.

export type Turn = {
  speaker: "user" | "twin";
  text: string;
  t: string; // mm:ss
  tactic?: string;
};

export type Insight = {
  kind: "leverage" | "mistake" | "tactic" | "tip";
  text: string;
};

export const persona = {
  name: "Dana Whitlock",
  role: "VP of Sales · Aperture Cloud",
  avatar: "DW",
  style: "Consultative, anchors high, trades concessions for term length.",
  objective: "Renew at list price; protect margin.",
  batna: "Strong inbound pipeline — can let the account churn.",
  reservation: "Will reach 15% off + 2-yr term under real pressure (hidden).",
  tactics: ["Anchor high", "Bundle to justify price", "Quarter-end urgency", "Trade for commitment"],
  pressure: ["Quarter-end quota", "Knows you evaluated a competitor", "Wants a public case study"],
};

export const transcript: Turn[] = [
  { speaker: "user", t: "00:04", text: "Thanks for hopping on, Dana. Before we talk renewal — we've been happy, but the budget reality this year means we need this number to come down meaningfully." },
  { speaker: "twin", t: "00:11", tactic: "Anchor high", text: "I appreciate the candor. Honestly, given the expansion in usage we've seen on your side, most accounts at your tier are renewing at list — I'd actually struggled to justify a discount to finance." },
  { speaker: "user", t: "00:24", text: "I hear you. But we've had a competitor come in 20% under your list for comparable scope. I'd rather stay — but not at a 20% premium." },
  { speaker: "twin", t: "00:33", tactic: "Probe the alternative", text: "Comparable scope? That's worth pressure-testing — their SSO and audit logging aren't at parity, and a migration is six weeks of your team's time. What's the all-in number they actually put in writing?" },
  { speaker: "user", t: "00:48", text: "It's in writing. And we've scoped the migration — it's real, but survivable. I want to find a reason to stay. Give me 25% and 20 added seats and we sign this week." },
  { speaker: "twin", t: "00:59", tactic: "Trade for commitment", text: "25% isn't a number I can take to finance on a one-year. If you'll go to a two-year term and let us publish a case study, I can get to a meaningful discount — that changes the math on my side." },
  { speaker: "user", t: "01:14", text: "A case study I can do. Two years only if the discount reflects the commitment — 18% off, 20 seats included, and a price lock for year two." },
  { speaker: "twin", t: "01:25", tactic: "Manufactured urgency", text: "If we close before quarter-end I can defend 15% plus the 20 seats and the year-two lock. The case study gets me there. Past Friday, I lose the quarter-end approval window." },
];

// Coach insight per user turn index (0-based on USER turns).
export const coachByUserTurn: Record<number, Insight[]> = {
  0: [
    { kind: "tip", text: "Strong open — you anchored on budget reality without naming a number first. Hold the silence." },
  ],
  1: [
    { kind: "leverage", text: "You introduced the competitor quote — that's your strongest lever. Don't let her reframe it as non-comparable without a counter." },
    { kind: "tactic", text: "Dana is anchoring high with 'list price' and social proof. Discount it; don't negotiate against her anchor." },
  ],
  2: [
    { kind: "mistake", text: "You revealed 'survivable' on migration — that softened your BATNA. Keep switching cost ambiguous." },
    { kind: "leverage", text: "Her ask for a case study is a tell: she wants this deal. Price the reference — don't give it free." },
  ],
  3: [
    { kind: "leverage", text: "She moved to 15% + seats + year-2 lock under quarter-end pressure — you're near her hidden floor. Trade the case study timing for the last points." },
    { kind: "tip", text: "Counter at 17% citing the 2-year commitment, concede the case study on signature, and you close above target." },
  ],
};

export const suggestedMove =
  "Counter: 17% off on the 2-year, 20 seats included, year-two price lock, case study delivered 30 days post-signature. You land between target ($90k) and her floor — and you keep the quarter-end clock as your leverage, not hers.";

// Deal-probability trajectory (one point per turn pair).
export const probabilitySeries = [0.34, 0.41, 0.38, 0.52, 0.49, 0.63, 0.71, 0.78];

export const leverage = [
  { label: "Competitor quote in writing", strength: 0.9 },
  { label: "Quarter-end quota pressure", strength: 0.82 },
  { label: "Case study they want", strength: 0.74 },
  { label: "Multi-year commitment to trade", strength: 0.66 },
];

// Persuasion analytics — live gauges (0..1).
export const persuasion = [
  { label: "Rapport", value: 0.72, delta: +0.04 },
  { label: "Anchoring control", value: 0.58, delta: +0.11 },
  { label: "Information edge", value: 0.64, delta: -0.06 },
  { label: "Momentum", value: 0.81, delta: +0.09 },
];

export const agents = [
  { name: "Twin", desc: "Role-plays Dana in character", state: "speaking" },
  { name: "Coach", desc: "Scoring your last move", state: "thinking" },
  { name: "Predictor", desc: "Updating outcome model", state: "thinking" },
  { name: "RAG Retriever", desc: "Pulled 3 tactics on competitive BATNA", state: "done" },
] as const;

export const retrievalFeed = [
  "Matched move: buyer cites competing quote",
  "Retrieved: 'Counter a competitor anchor with switching cost'",
  "Retrieved: 'Price the reference — never give it free'",
  "Retrieved: 'Quarter-end urgency cuts both ways'",
];

// Knowledge graph — relationships between the entities in play.
export const graph = {
  nodes: [
    { id: "you", label: "You", x: 0.5, y: 0.5, kind: "self" },
    { id: "dana", label: "Dana", x: 0.8, y: 0.28, kind: "twin" },
    { id: "competitor", label: "Competitor quote", x: 0.2, y: 0.26, kind: "lever" },
    { id: "casestudy", label: "Case study", x: 0.78, y: 0.74, kind: "lever" },
    { id: "quarter", label: "Quarter-end", x: 0.5, y: 0.12, kind: "lever" },
    { id: "term", label: "2-yr term", x: 0.22, y: 0.74, kind: "trade" },
    { id: "seats", label: "+20 seats", x: 0.5, y: 0.88, kind: "trade" },
  ],
  edges: [
    { from: "you", to: "dana", label: "negotiating" },
    { from: "competitor", to: "you", label: "leverage" },
    { from: "dana", to: "casestudy", label: "wants" },
    { from: "quarter", to: "dana", label: "pressures" },
    { from: "you", to: "term", label: "can offer" },
    { from: "you", to: "seats", label: "asking" },
    { from: "term", to: "dana", label: "unlocks discount" },
  ],
};

export const replaySteps = [
  { t: "00:24", label: "Competitor lever introduced", prob: 0.38, note: "Pivotal — strongest leverage on the table." },
  { t: "00:48", label: "Migration called 'survivable'", prob: 0.38, note: "Mistake: softened your walk-away.", flag: true },
  { t: "00:59", label: "Case-study tell surfaces", prob: 0.52, note: "Dana reveals she wants the deal." },
  { t: "01:25", label: "Floor reached: 15% + lock", prob: 0.78, note: "Near her hidden reservation." },
];

export const outcome = {
  probability: 0.78,
  favorability: 0.71,
  summary:
    "Likely close at ~16–17% discount on a 2-year term with 20 seats and a year-two price lock, in exchange for a published case study. Lands between your target and her floor.",
};
