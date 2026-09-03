from datetime import datetime
from sqlalchemy.orm import Session

from ..models.incident import Incident, Investigation
from ..providers.factory import get_provider
from .evidence_builder import EvidenceBuilder


class InvestigationService:
    """Orchestrates the full investigation pipeline."""

    def __init__(self, db: Session):
        self.db               = db
        self.evidence_builder = EvidenceBuilder(db)

    async def investigate(self, incident_id_str: str) -> Investigation:
        inc = (
            self.db.query(Incident)
            .filter(Incident.incident_id == incident_id_str)
            .first()
        )
        if not inc:
            raise ValueError(f"Incident {incident_id_str} not found")

        inc.status     = "INVESTIGATING"
        inc.updated_at = datetime.utcnow()
        self.db.commit()

        evidence_package = self.evidence_builder.build_evidence_package(
            incident_id   = incident_id_str,
            service       = inc.service,
            incident_start= inc.start_time,
        )

        provider = get_provider()
        result   = await provider.investigate(evidence_package)

        existing = (
            self.db.query(Investigation)
            .filter(Investigation.incident_id == inc.id)
            .first()
        )

        if existing:
            existing.root_cause          = result.incident_summary.get("primary_root_cause")
            existing.confidence_score    = result.incident_summary.get("confidence_score")
            existing.causal_narrative    = result.causal_narrative
            existing.evidence_package    = evidence_package
            existing.hypotheses          = result.evaluated_hypotheses
            existing.recommended_actions = result.recommended_actions
            existing.updated_at          = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            investigation = Investigation(
                incident_id          = inc.id,
                root_cause           = result.incident_summary.get("primary_root_cause"),
                confidence_score     = result.incident_summary.get("confidence_score"),
                causal_narrative     = result.causal_narrative,
                evidence_package     = evidence_package,
                hypotheses           = result.evaluated_hypotheses,
                recommended_actions  = result.recommended_actions,
            )
            self.db.add(investigation)
            self.db.commit()
            self.db.refresh(investigation)
            return investigation
