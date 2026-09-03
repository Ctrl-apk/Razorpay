from typing import Dict, Any
import json
import re
from .base import AIProvider, InvestigationResult
from ..config import settings

try:
    import anthropic as anthropic_lib
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

SYSTEM_PROMPT = """You are an expert Systems Reliability Engineer performing root-cause analysis on software incidents.

You receive pre-processed deterministic telemetry as JSON.

Your analysis must be strictly grounded in the supplied evidence.

CRITICAL RULES:
1. NEVER invent metrics, logs, traces, timestamps, deployments, services, or infrastructure events
2. If information is unavailable, use "UNKNOWN"
3. Separate OBSERVED FACTS from INFERRED CONCLUSIONS
4. Evaluate competing hypotheses
5. If evidence is insufficient, say so
6. You do not control production systems - recommend actions but never execute them
7. Return ONLY valid JSON in the exact schema

Return JSON with keys: incident_summary, causal_narrative, evidence_points, evaluated_hypotheses, recommended_actions"""


class AnthropicInvestigator(AIProvider):
    """Anthropic Claude-backed investigator."""

    def __init__(self):
        if not ANTHROPIC_AVAILABLE:
            raise RuntimeError("anthropic library not installed")
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        self.client = anthropic_lib.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-3-opus-20240229"

    async def investigate(self, evidence_package: Dict[str, Any]) -> InvestigationResult:
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=2500,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this incident:\n\n{json.dumps(evidence_package, indent=2)}",
                }
            ],
        )

        raw = message.content[0].text
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError("Could not extract JSON from Anthropic response")

        data = json.loads(match.group())
        return InvestigationResult(**data)
