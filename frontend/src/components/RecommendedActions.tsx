import { ArrowRight } from "lucide-react";
import type { RecommendedAction, Priority } from "../types";

const priorityStyle: Record<Priority, string> = {
  HIGH:   "text-red-400 bg-red-500/10 border-red-500/30",
  MEDIUM: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
  LOW:    "text-blue-400 bg-blue-500/10 border-blue-500/30",
};

export default function RecommendedActions({ actions }: { actions: RecommendedAction[] }) {
  if (!actions || actions.length === 0) {
    return <div className="text-slate-500 text-sm">No recommended actions</div>;
  }

  return (
    <div className="space-y-3">
      {actions.map((a, idx) => (
        <div key={idx} className="flex gap-4 rounded-lg bg-[#0f1629] border border-[#1e2a45] p-4">
          <div className="flex-shrink-0 mt-0.5">
            <span className={`text-xs font-bold px-2 py-0.5 rounded border ${priorityStyle[a.priority]}`}>
              {a.priority}
            </span>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <ArrowRight size={14} className="text-blue-400" />
              <span className="text-white text-sm font-semibold">{a.action}</span>
            </div>
            <p className="text-slate-400 text-xs">{a.details}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
