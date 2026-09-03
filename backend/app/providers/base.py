from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel


class InvestigationResult(BaseModel):
    incident_summary: Dict[str, Any]
    causal_narrative: str
    evidence_points: list
    evaluated_hypotheses: list
    recommended_actions: list


class AIProvider(ABC):
    """Base AI provider interface."""
    
    @abstractmethod
    async def investigate(self, evidence_package: Dict[str, Any]) -> InvestigationResult:
        """Investigate an incident using the evidence package."""
        pass
