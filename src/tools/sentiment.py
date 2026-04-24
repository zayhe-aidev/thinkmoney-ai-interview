"""Tone detection tool for thinkmoney customer service triage."""

import json

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

_TONE_SYSTEM_PROMPT = (
    'Classify the tone of this customer message. '
    'Respond with valid JSON only: '
    '{"tone": "frustrated|neutral|satisfied", "confidence": 0.0-1.0, "reason": "brief explanation"}'
)

_llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)


@tool
def detect_tone(message: str) -> str:
    """Classify the tone of a customer message as frustrated, neutral, or satisfied.
    Use this before routing to a specialist agent to detect if HITL escalation is needed.

    Args:
        message: The latest customer message to classify.
    """
    try:
        response = _llm.invoke([
            SystemMessage(content=_TONE_SYSTEM_PROMPT),
            HumanMessage(content=message),
        ])
        return response.content
    except Exception:
        return json.dumps({"tone": "neutral", "confidence": 0.0, "reason": "classification failed"})
