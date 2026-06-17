// Live backend client. Judge Mode (demo.ts) is the default experience and needs
// none of this; this is the "Live mode" path that talks to the FastAPI service.
//
// Base URL comes from VITE_API_BASE_URL, baked at build time on Render (it is a
// public URL, not a secret). If unset, isLive() is false and the UI stays on
// the scripted Judge-Mode data — so a missing backend never breaks the demo.

const BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export const isLive = () => BASE.length > 0;

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`API ${path} → ${res.status} ${await res.text()}`);
  return res.json() as Promise<T>;
}

export type PersonaDTO = Record<string, unknown>;
export type TurnResultDTO = {
  twin: string;
  coach: { insights: { kind: string; text: string }[]; suggested_move?: string } | null;
  prediction: { deal_probability: number; predicted_outcome?: string; drivers?: unknown } | null;
};

export const api = {
  health: () => call<{ status: string }>("/health"),

  createSession: (body: {
    title: string;
    scenario: string;
    user_goal?: string;
    user_batna?: string;
    target_price?: number;
    reservation_price?: number;
    persona_intel?: string;
  }) => call<{ session_id: number; persona: PersonaDTO }>("/sessions", {
    method: "POST",
    body: JSON.stringify(body),
  }),

  turn: (sessionId: number, text: string) =>
    call<TurnResultDTO>(`/sessions/${sessionId}/turn`, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),

  timeline: (sessionId: number) => call<unknown[]>(`/sessions/${sessionId}/timeline`),
  review: (sessionId: number) => call<Record<string, unknown>>(`/sessions/${sessionId}/review`),
  whatIf: (sessionId: number, upToTurnIndex: number, alternativeLine: string) =>
    call<Record<string, unknown>>(`/sessions/${sessionId}/whatif`, {
      method: "POST",
      body: JSON.stringify({ up_to_turn_index: upToTurnIndex, alternative_line: alternativeLine }),
    }),

  generatePersona: (intel: string, scenario = "") =>
    call<PersonaDTO>("/personas/generate", {
      method: "POST",
      body: JSON.stringify({ intel, scenario }),
    }),
};
