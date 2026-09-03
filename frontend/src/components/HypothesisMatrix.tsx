import { CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import type { Hypothesis, HypothesisStatus } from "../types";

const statusConfig: Record<HypothesisStatus, { label: string; color: string; icon: React.ReactNode }> = {
  MOST_LIKELY: {
    label: "MOST LIKELY",
    color: "text-green-400 bg-green-500/10 border-green-500/30",
    icon: <CheckCircle2 size={16} className="text-green-400" />,
  },
  LIKELY: {
    label: "LIKELY",
    color: "text-blue-400 bg-blue-500/10 border-blue-500/30",
    icon: <CheckCircle2 size={16} className="text-blue-400" />,
  },
  UNLIKELY: {
    label: "UNLIKELY",
    color: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
    icon: <AlertCircle size={16} className="text-yellow-400" />,
  },
  REJECTED: {
    label: "REJECTED",
    color: "text-red-400 bg-red-500/10 border-red-500/30",
    icon: <XCircle size={16} className="text-red-400" />,
  },
};

interface Props {
  hypotheses: Hypothesis[];
}

export default function HypothesisMatrix({ hypotheses }: Props) {
  if (!hypotheses || hypotheses.length === 0) {
    return <div className="text-slate-500 text-sm">No hypotheses available</div>;
  }

  return (
    <div className="space-y-3">
      {hypotheses.map((h, idx) => {
        const cfg = statusConfig[h.status] ?? statusConfig.UNLIKELY;
        return (
          <div
            key={idx}
            className={`rounded-lg border p-4 ${
              h.status === "MOST_LIKELY"
                ? "border-green-500/30 bg-green-500/5"
                : h.status === "REJECTED"
                ? "border-red-500/20 bg-red-500/5 opacity-75"
                : "border-[#1e2a45] bg-[#0f1629]"
            }`}
          >
            <div className="flex items-start justify-between gap-4 mb-3">
              <div className="flex items-center gap-2">
                {cfg.icon}
                <span className="text-white font-semibold text-sm">{h.hypothesis_name}</span>
              </div>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${cfg.color}`}>
                {cfg.label}
              </span>
            </div>

            <p className="text-slate-400 text-sm mb-3">{h.reasoning}</p>

            <div className="grid grid-cols-2 gap-3 text-xs">
              {h.evidence_for.length > 0 && (
                <div>
                  <div className="text-green-400 font-semibold mb-1">Evidence For</div>
                  <ul className="space-y-1">
                    {h.evidence_for.map((e, i) => (
                      <li key={i} className="text-slate-400 flex items-start gap-1">
                        <span className="text-green-500 mt-0.5">✓</span> {e}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {h.evidence_against.length > 0 && (
                <div>
                  <div className="text-red-400 font-semibold mb-1">Evidence Against</div>
                  <ul className="space-y-1">
                    {h.evidence_against.map((e, i) => (
                      <li key={i} className="text-slate-400 flex items-start gap-1">
                        <span className="text-red-500 mt-0.5">✗</span> {e}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
