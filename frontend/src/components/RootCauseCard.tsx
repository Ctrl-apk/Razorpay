import { ShieldAlert, CheckCircle, ExternalLink } from "lucide-react";
import type { Investigation } from "../types";
import ConfidenceBar from "./ConfidenceBar";

interface Props {
  investigation: Investigation;
  onViewEvidence?: () => void;
  onViewHypotheses?: () => void;
}

export default function RootCauseCard({ investigation, onViewEvidence, onViewHypotheses }: Props) {
  const confidence = investigation.confidence_score ?? 0;
  const severity = confidence >= 0.8 ? "HIGH" : confidence >= 0.6 ? "MEDIUM" : "LOW";

  return (
    <div className="rounded-xl border border-blue-500/30 bg-gradient-to-br from-[#0f1629] to-[#0a1020] p-6">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <ShieldAlert size={18} className="text-blue-400" />
        <span className="text-xs font-bold text-blue-400 tracking-widest uppercase">
          Most Likely Root Cause
        </span>
      </div>

      {/* Root cause title */}
      <h2 className="text-xl font-bold text-white mb-1">
        {investigation.root_cause ?? "Under Investigation"}
      </h2>

      {/* Confidence + Severity row */}
      <div className="flex items-center gap-6 mb-4">
        <div className="flex-1">
          <div className="text-xs text-slate-400 mb-1">Confidence</div>
          <ConfidenceBar score={confidence} />
        </div>
        <div>
          <div className="text-xs text-slate-400 mb-1">Severity</div>
          <span
            className={`text-sm font-bold ${
              severity === "HIGH" ? "text-orange-400" : severity === "MEDIUM" ? "text-yellow-400" : "text-blue-400"
            }`}
          >
            {severity}
          </span>
        </div>
      </div>

      {/* Narrative */}
      {investigation.causal_narrative && (
        <p className="text-slate-300 text-sm leading-relaxed mb-5 border-l-2 border-blue-500/50 pl-3">
          {investigation.causal_narrative}
        </p>
      )}

      {/* Evidence summary */}
      {investigation.hypotheses && investigation.hypotheses.length > 0 && (
        <div className="mb-5">
          <div className="text-xs text-slate-400 uppercase tracking-wider mb-2">Supporting Evidence</div>
          <ul className="space-y-1">
            {investigation.hypotheses
              .find((h) => h.status === "MOST_LIKELY")
              ?.evidence_for.slice(0, 4)
              .map((e, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                  <CheckCircle size={14} className="text-green-400 mt-0.5 flex-shrink-0" />
                  {e}
                </li>
              ))}
          </ul>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={onViewEvidence}
          className="flex items-center gap-1.5 px-4 py-2 bg-blue-600/20 hover:bg-blue-600/40 border border-blue-500/30 rounded-lg text-blue-300 text-sm transition-colors"
        >
          <ExternalLink size={14} />
          View Evidence
        </button>
        <button
          onClick={onViewHypotheses}
          className="flex items-center gap-1.5 px-4 py-2 bg-[#1e2a45] hover:bg-[#253352] border border-[#1e2a45] rounded-lg text-slate-300 text-sm transition-colors"
        >
          View Hypotheses
        </button>
      </div>
    </div>
  );
}
