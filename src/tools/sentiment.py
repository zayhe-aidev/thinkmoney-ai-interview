"""Tone detection tool factory for thinkmoney customer service."""

import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

_TONE_SYSTEM_PROMPT = """Classify the tone of this customer message.
Respond with valid JSON only, no other text:
{"tone": "frustrated|neutral|satisfied", "confidence": 0.0-1.0, "reason": "brief explanation"}"""


def make_detect_tone_tool(llm):
    @tool
    def detect_tone(message: str) -> str:
        """Classify the tone of a customer message as frustrated, neutral, or satisfied.
        Use this before routing to a specialist agent to detect if HITL escalation is needed.

        Args:
            message: The latest customer message to classify.
        """
        try:
            response = llm.invoke([
                SystemMessage(content=_TONE_SYSTEM_PROMPT),
                HumanMessage(content=message),
            ])
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            json.loads(content)  # validate — raises if malformed
            return content
        except Exception:
            return json.dumps({"tone": "neutral", "confidence": 0.0, "reason": "classification failed"})

    return detect_tone
