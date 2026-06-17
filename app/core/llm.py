"""Thin wrapper around the Anthropic SDK.

Every agent in the system (twin, coach, predictor, persona generator) talks to
Claude through this one client. Centralizing it means model IDs, adaptive
thinking, streaming, and structured-output parsing are configured in exactly
one place.

Design notes
------------
* Default model is ``claude-opus-4-8`` with adaptive thinking — the recommended
  setup for anything that requires reasoning (which a negotiation twin does).
* ``stream()`` is used for the twin's reply so the UI can render token-by-token.
* ``parse()`` uses the SDK's structured-output path (``messages.parse`` with a
  Pydantic model) so the coach/predictor return validated objects, not text we
  have to regex.
"""
from __future__ import annotations

from typing import Iterator, Sequence, Type, TypeVar

import anthropic
from pydantic import BaseModel

from app.core.config import settings

T = TypeVar("T", bound=BaseModel)

Message = dict  # {"role": "user"|"assistant", "content": str | list}


class LLMClient:
    def __init__(self, model: str | None = None, effort: str | None = None):
        # The SDK resolves ANTHROPIC_API_KEY from the environment automatically.
        self._client = anthropic.Anthropic()
        self.model = model or settings.model
        self.effort = effort or settings.effort

    # ------------------------------------------------------------------ #
    # Plain completion                                                    #
    # ------------------------------------------------------------------ #
    def complete(
        self,
        system: str,
        messages: Sequence[Message],
        *,
        max_tokens: int = 2000,
        thinking: bool = True,
    ) -> str:
        """One-shot completion, returns the concatenated text blocks."""
        kwargs = self._base_kwargs(system, messages, max_tokens, thinking)
        resp = self._client.messages.create(**kwargs)
        return "".join(b.text for b in resp.content if b.type == "text").strip()

    # ------------------------------------------------------------------ #
    # Streaming completion (used for the twin's spoken reply)             #
    # ------------------------------------------------------------------ #
    def stream(
        self,
        system: str,
        messages: Sequence[Message],
        *,
        max_tokens: int = 2000,
        thinking: bool = True,
    ) -> Iterator[str]:
        """Yield text deltas as they arrive."""
        kwargs = self._base_kwargs(system, messages, max_tokens, thinking)
        with self._client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text

    # ------------------------------------------------------------------ #
    # Structured output (used for coach / predictor / persona generator)  #
    # ------------------------------------------------------------------ #
    def parse(
        self,
        system: str,
        messages: Sequence[Message],
        schema: Type[T],
        *,
        max_tokens: int = 3000,
    ) -> T:
        """Return a validated instance of ``schema``.

        Structured outputs are incompatible with extended thinking display but
        work fine alongside the model; we keep thinking off here for a tight,
        deterministic shape.
        """
        resp = self._client.messages.parse(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=list(messages),
            output_format=schema,
        )
        parsed = resp.parsed_output
        if parsed is None:
            raise RuntimeError(
                f"Structured parse returned no output (stop_reason={resp.stop_reason})"
            )
        return parsed

    # ------------------------------------------------------------------ #
    def _base_kwargs(self, system, messages, max_tokens, thinking) -> dict:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": list(messages),
            "output_config": {"effort": self.effort},
        }
        if thinking:
            kwargs["thinking"] = {"type": "adaptive"}
        return kwargs


# Shared default client. Agents can construct their own (e.g. on the fast model)
# but most reuse this.
llm = LLMClient()
