"""Persona schema — the structured definition of a counterparty's digital twin.

This is the contract between the persona generator (Phase 2) and the
negotiation engine (Phase 1). The engine turns a PersonaProfile into the
twin's system prompt; the generator produces one from notes/documents.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class PersonaProfile(BaseModel):
    name: str = Field(description="The counterparty's name.")
    role: str = Field(description="Their role/title and the org they represent.")
    objective: str = Field(description="What they are trying to achieve in this negotiation.")
    batna: str = Field(
        description="Their best alternative to a negotiated agreement — their walk-away."
    )
    reservation: str = Field(
        default="",
        description="Their true bottom line (hidden from the user; the twin must protect it).",
    )
    personality: str = Field(
        description="Personality and decision-making style (e.g. analytical, relationship-driven, impatient)."
    )
    communication_style: str = Field(
        description="How they talk: terse vs verbose, formal vs casual, aggressive vs collaborative."
    )
    tactics: list[str] = Field(
        default_factory=list,
        description="Negotiation tactics this person tends to use (anchoring, deadline pressure, good-cop, etc.).",
    )
    tells: list[str] = Field(
        default_factory=list,
        description="Behavioral tells that signal when they're bluffing, anxious, or ready to concede.",
    )
    pressure_points: list[str] = Field(
        default_factory=list,
        description="Their constraints/needs the user can press on for leverage.",
    )

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "PersonaProfile":
        return cls(**data)


def default_twin() -> PersonaProfile:
    """A ready-to-demo counterparty so Phase 1 runs before the generator exists.

    Scenario: you're negotiating an enterprise SaaS renewal; the twin is the
    vendor's tough-but-fair VP of Sales.
    """
    return PersonaProfile(
        name="Dana Whitlock",
        role="VP of Sales at Aperture Cloud (enterprise SaaS vendor)",
        objective="Renew the customer at list price or higher, minimize discount, protect margin.",
        batna="Plenty of inbound demand; can let this account churn without missing quota.",
        reservation="Will go down to a 15% discount and a 2-year term if pushed hard, but never says so.",
        personality="Confident, warm on the surface, quietly competitive. Anchors high and waits.",
        communication_style="Polished, consultative, uses social proof and scarcity. Rarely concedes first.",
        tactics=[
            "Anchor high with list price",
            "Bundle features to justify price",
            "Manufacture urgency around quarter-end",
            "Trade concessions for longer commitments",
        ],
        tells=[
            "Gets specific about ROI numbers when genuinely worried about losing the deal",
            "Offers to 'check with finance' when actually willing to move",
        ],
        pressure_points=[
            "Quarter-end quota pressure",
            "Knows the customer has evaluated a competitor",
            "Wants a public case study / reference",
        ],
    )
