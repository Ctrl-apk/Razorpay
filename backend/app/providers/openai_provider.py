from typing import Dict, Any
import json
import re
from .base import AIProvider, InvestigationResult
from ..config import settings

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

SYSTEM_PROMPT = """You are an expert Systems Reliability Engineer performing root-cause analysis on software incidents.

You receive pre-processed deterministic telemetry as JSON.

Your analysis must be strictly grounded in the supplied evidence.

CRITICAL RULES:
1. NEVER invent metrics, logs, traces, timestamps, deployments, services, or infrastructure events
2. If information is unavailable, use "UNKNOWN"
3. Separate OBSERVED FACTS from INFERRED CONCLUSIONS
4. Evaluate competing hypotheses
5. Explain why the most likely hypothesis is supported
6. Explain why alternative hypotheses are rejected or considered unlikely
7. If evidence is insufficient, say so
8. You do not control production systems - recommend actions but never execute them
9. Return ONLY valid JSON in the exact schema requested

Return JSON:
{
  "incident_summary": {
    "title": "string",
    "confidence_score": 0.0-1.0,
    "severity": "LOW|MEDIUM|HIGH|CRITICAL",
    "primary_root_cause": "string"
  },
  "causal_narrative": "string",
  "evidence_points": [
    {"type": "metric|log|deployment", "observation": "string", "supporting": true}
  ],
  "evaluated_hypotheses": [
    {
      "hypothesis_name": "string",
      "status": "MOST_LIKELY|UNLIKELY|REJECTED",
      "reasoning": "string",
      "evidence_for": ["string"],
      "evidence_against": ["string"]
    }
  ],
  "recommended_actions": [
    {"priority": "HIGH|MEDIUM|LOW", "action": "string", "details": "string"}
  ]
}"""


class OpenAIInvestigator(AIProvider):
    """OpenAI-backed investigator."""

    def __init__(self):
        if not OPENAI_AVAILABLE:
            raise RuntimeError("openai library not installed")
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4"

    async def investigate(self, evidence_package: Dict[str, Any]) -> InvestigationResult:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this incident:\n\n{json.dumps(evidence_package, indent=2)}"},
            ],
            temperature=0.2,
            max_tokens=2500,
        )

        raw = response.choices[0].message.content
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError("Could not extract JSON from OpenAI response")

        data = json.loads(match.group())
        return InvestigationResult(**data)
