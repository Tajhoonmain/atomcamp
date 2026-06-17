"""Brand theme for the dashboard — the Mirror Mark identity.

Palette (Iris): primary #4F46E5, accent teal #2DD4BF, navy bg #0A0E1A.
Centralized here so charts and CSS stay consistent.
"""
from __future__ import annotations

PRIMARY = "#4F46E5"
ACCENT = "#2DD4BF"
BG = "#0A0E1A"
SURFACE = "#12172A"
BORDER = "#222842"
TEXT = "#E6E8F0"
MUTED = "#8A90A6"

# The Mirror Mark: two mirrored uprights + a teal leverage diagonal forming an N.
LOGO_SVG = """
<svg width="160" height="48" viewBox="0 0 320 96" xmlns="http://www.w3.org/2000/svg">
  <g transform="translate(8,14)">
    <rect x="20" y="14" width="16" height="72" rx="8" fill="#FFFFFF"/>
    <rect x="64" y="14" width="16" height="72" rx="8" fill="#FFFFFF"/>
    <line x1="28" y1="22" x2="72" y2="78" stroke="#2DD4BF" stroke-width="15" stroke-linecap="round"/>
  </g>
  <text x="104" y="44" font-family="Segoe UI, Inter, sans-serif" font-size="26"
        font-weight="600" fill="#FFFFFF" letter-spacing="-0.5">Negotiation</text>
  <text x="104" y="74" font-family="Segoe UI, Inter, sans-serif" font-size="26"
        font-weight="400" fill="#8A90A6" letter-spacing="-0.5">Digital Twin</text>
</svg>
"""

ICON_SVG = """
<svg width="40" height="40" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100" rx="22" fill="#0A0E1A"/>
  <g transform="translate(0,0)">
    <rect x="20" y="14" width="16" height="72" rx="8" fill="#FFFFFF"/>
    <rect x="64" y="14" width="16" height="72" rx="8" fill="#FFFFFF"/>
    <line x1="28" y1="22" x2="72" y2="78" stroke="#2DD4BF" stroke-width="15" stroke-linecap="round"/>
  </g>
</svg>
"""


def inject_css() -> str:
    """Global CSS to push Streamlit toward the dark, premium brand look."""
    return f"""
    <style>
      .stApp {{ background: {BG}; color: {TEXT}; }}
      section[data-testid="stSidebar"] {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}
      h1, h2, h3, h4 {{ color: {TEXT}; letter-spacing: -0.3px; }}
      .ndt-card {{
        background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px;
        padding: 16px 18px; margin-bottom: 12px;
      }}
      .ndt-pill {{
        display: inline-block; padding: 2px 10px; border-radius: 999px;
        font-size: 12px; font-weight: 600; margin-right: 6px;
      }}
      .ndt-leverage {{ background: rgba(45,212,191,0.15); color: {ACCENT}; }}
      .ndt-mistake  {{ background: rgba(239,68,68,0.15);  color: #F87171; }}
      .ndt-tactic   {{ background: rgba(79,70,229,0.18);  color: #A5B4FC; }}
      .ndt-tip      {{ background: rgba(148,163,184,0.15); color: {MUTED}; }}
      .ndt-muted {{ color: {MUTED}; font-size: 13px; }}
      .stChatMessage {{ background: transparent; }}
      .stButton>button {{
        background: {PRIMARY}; color: white; border: none; border-radius: 10px;
        font-weight: 600;
      }}
      .stButton>button:hover {{ background: #4338CA; }}
    </style>
    """
