"""Phase 7 — Negotiation Digital Twin dashboard.

Dark-mode-first Streamlit app. Three tabs:
  * Negotiate — live chat against the twin, streaming replies.
  * Analytics — outcome-probability curve, coach insights, persona card.
  * Replay    — graded post-mortem + what-if simulator.

Run:  streamlit run ui/streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the repo importable when launched via `streamlit run ui/streamlit_app.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from app.negotiation.engine import NegotiationEngine  # noqa: E402
from app.twin.persona import default_twin  # noqa: E402
from ui import theme  # noqa: E402

st.set_page_config(page_title="Negotiation Digital Twin", page_icon="N", layout="wide")
st.markdown(theme.inject_css(), unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# State
# --------------------------------------------------------------------------- #
def _state():
    ss = st.session_state
    ss.setdefault("engine", None)
    ss.setdefault("session_id", None)
    ss.setdefault("persona", default_twin())
    ss.setdefault("messages", [])         # [{role, content}]
    ss.setdefault("insights", [])         # latest coach insights
    ss.setdefault("suggested_move", "")
    ss.setdefault("prob_history", [])     # [(turn_no, probability)]
    return ss


ss = _state()


# --------------------------------------------------------------------------- #
# Sidebar — brand + session setup
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown(theme.LOGO_SVG, unsafe_allow_html=True)
    st.markdown(
        f"<div class='ndt-muted'>Win the conversation before it happens.</div>",
        unsafe_allow_html=True,
    )
    st.divider()
    st.subheader("New negotiation")
    title = st.text_input("Title", "SaaS renewal vs Dana Whitlock")
    scenario = st.text_area(
        "Scenario",
        "Annual enterprise SaaS renewal. You pay $120k/yr and want a discount plus "
        "more seats. The vendor wants to renew at list price.",
        height=90,
    )
    user_goal = st.text_input("Your goal", "Cut price 25% and add 20 seats free.")
    user_batna = st.text_input("Your BATNA", "A competitor quoted 20% less, 6-week migration.")
    col_a, col_b = st.columns(2)
    target = col_a.number_input("Target $", value=90000, step=5000)
    reservation = col_b.number_input("Walk-away $", value=105000, step=5000)
    live_coach = st.toggle("Live coach + prediction", value=True)
    use_rag = st.toggle("RAG-augmented twin", value=False, help="Requires `python -m scripts.seed_knowledge`.")

    if st.button("Start negotiation", use_container_width=True):
        engine = NegotiationEngine(
            enable_rag=use_rag, enable_coach=live_coach, enable_prediction=live_coach
        )
        sid = engine.create_session(
            title=title,
            scenario=scenario,
            persona=default_twin(),
            user_goal=user_goal,
            user_batna=user_batna,
            target_price=float(target),
            reservation_price=float(reservation),
        )
        ss.engine = engine
        ss.session_id = sid
        ss.messages = []
        ss.insights = []
        ss.prob_history = []
        ss.suggested_move = ""
        st.rerun()


def _severity_pill(kind: str) -> str:
    return {
        "leverage": "ndt-leverage",
        "mistake": "ndt-mistake",
        "tactic": "ndt-tactic",
        "tip": "ndt-tip",
    }.get(kind, "ndt-tip")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if ss.engine is None or ss.session_id is None:
    st.markdown(theme.ICON_SVG, unsafe_allow_html=True)
    st.title("Negotiation Digital Twin")
    st.markdown(
        "<p class='ndt-muted'>Configure a scenario in the sidebar and press "
        "<b>Start negotiation</b> to rehearse against your AI counterparty.</p>",
        unsafe_allow_html=True,
    )
    st.stop()

tab_negotiate, tab_analytics, tab_replay = st.tabs(["Negotiate", "Analytics", "Replay"])


# ---------------------------- Negotiate ------------------------------------ #
with tab_negotiate:
    persona = ss.persona
    st.markdown(
        f"<div class='ndt-card'><b>{persona.name}</b> &middot; "
        f"<span class='ndt-muted'>{persona.role}</span></div>",
        unsafe_allow_html=True,
    )

    col_chat, col_coach = st.columns([3, 2])

    with col_chat:
        for m in ss.messages:
            with st.chat_message("user" if m["role"] == "user" else "assistant"):
                st.write(m["content"])

        prompt = st.chat_input("Your move...")
        if prompt:
            ss.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            with st.chat_message("assistant"):
                placeholder = st.empty()
                acc: list[str] = []

                def _on_delta(d: str):
                    acc.append(d)
                    placeholder.markdown("".join(acc) + "▌")

                try:
                    result = ss.engine.respond_stream(ss.session_id, prompt, on_delta=_on_delta)
                    placeholder.markdown(result.twin_text)
                    ss.messages.append({"role": "assistant", "content": result.twin_text})
                    if result.coach:
                        ss.insights = [i.model_dump() for i in result.coach.insights]
                        ss.suggested_move = result.coach.suggested_move
                    if result.prediction:
                        ss.prob_history.append(
                            (len(ss.prob_history) + 1, result.prediction.deal_probability)
                        )
                except Exception as e:  # surfaces missing API key etc.
                    placeholder.error(f"Engine error: {e}")

    with col_coach:
        st.markdown("#### Coach")
        if ss.suggested_move:
            st.markdown(
                f"<div class='ndt-card'><span class='ndt-pill ndt-leverage'>next move</span><br>"
                f"{ss.suggested_move}</div>",
                unsafe_allow_html=True,
            )
        if ss.insights:
            for ins in ss.insights:
                st.markdown(
                    f"<div class='ndt-card'><span class='ndt-pill {_severity_pill(ins['type'])}'>"
                    f"{ins['type']}</span> {ins['content']}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown("<span class='ndt-muted'>Coaching appears after your first move.</span>",
                        unsafe_allow_html=True)


# ---------------------------- Analytics ------------------------------------ #
with tab_analytics:
    st.markdown("#### Deal probability over time")
    if ss.prob_history:
        xs = [t for t, _ in ss.prob_history]
        ys = [round(p * 100, 1) for _, p in ss.prob_history]
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=xs, y=ys, mode="lines+markers",
                line=dict(color=theme.ACCENT, width=3),
                marker=dict(color=theme.PRIMARY, size=8),
                fill="tozeroy", fillcolor="rgba(45,212,191,0.12)",
            )
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color=theme.TEXT, height=320, yaxis=dict(range=[0, 100], title="P(deal) %"),
            xaxis=dict(title="Turn"), margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.metric("Current deal probability", f"{ys[-1]:.0f}%")
    else:
        st.markdown("<span class='ndt-muted'>Enable the live coach and take a turn to populate "
                    "predictions.</span>", unsafe_allow_html=True)

    st.markdown("#### Counterparty profile")
    p = ss.persona
    st.markdown(
        f"<div class='ndt-card'><b>{p.name}</b> — {p.role}<br>"
        f"<span class='ndt-muted'>Style:</span> {p.communication_style}<br>"
        f"<span class='ndt-muted'>Tactics:</span> {', '.join(p.tactics)}<br>"
        f"<span class='ndt-muted'>Pressure points:</span> {', '.join(p.pressure_points)}</div>",
        unsafe_allow_html=True,
    )


# ---------------------------- Replay --------------------------------------- #
with tab_replay:
    st.markdown("#### Post-mortem review")
    if st.button("Generate review"):
        from app.replay.engine import ReplayEngine

        try:
            review = ReplayEngine().review(ss.session_id)
            st.markdown(
                f"<div class='ndt-card'><h2 style='margin:0'>Grade: {review.overall_grade}</h2>"
                f"<p>{review.summary}</p></div>",
                unsafe_allow_html=True,
            )
            if review.biggest_mistakes:
                st.markdown("**Biggest mistakes**")
                for m in review.biggest_mistakes:
                    st.markdown(f"- {m}")
            if review.alternatives:
                st.markdown("**Stronger lines**")
                for alt in review.alternatives:
                    st.markdown(
                        f"<div class='ndt-card'><span class='ndt-muted'>You said:</span> "
                        f"{alt.original}<br><span class='ndt-pill ndt-leverage'>better</span> "
                        f"{alt.better_line}<br><span class='ndt-muted'>{alt.why}</span></div>",
                        unsafe_allow_html=True,
                    )
        except Exception as e:
            st.error(f"Review failed: {e}")

    st.divider()
    st.markdown("#### What-if simulator")
    user_turns = [i for i, m in enumerate(ss.messages) if m["role"] == "user"]
    if user_turns:
        idx = st.selectbox("Replay from your turn #", user_turns, format_func=lambda i: f"Turn {user_turns.index(i)+1}")
        alt_line = st.text_input("What if you had said...")
        if st.button("Simulate") and alt_line:
            from app.replay.engine import ReplayEngine

            try:
                res = ReplayEngine().what_if(ss.session_id, user_turns.index(idx), alt_line)
                st.markdown(
                    f"<div class='ndt-card'><span class='ndt-muted'>{ss.persona.name} would reply:</span>"
                    f"<br>{res.twin_response}</div>",
                    unsafe_allow_html=True,
                )
                st.metric("Resulting deal probability", f"{res.deal_probability*100:.0f}%")
                st.caption(res.predicted_outcome)
            except Exception as e:
                st.error(f"Simulation failed: {e}")
    else:
        st.markdown("<span class='ndt-muted'>Take a few turns first, then simulate alternatives.</span>",
                    unsafe_allow_html=True)
