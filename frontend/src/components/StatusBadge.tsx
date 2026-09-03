import type { IncidentStatus } from "../types";

const map: Record<IncidentStatus, string> = {
  ACTIVE:        "bg-red-500/20 text-red-400 border border-red-500/30",
  INVESTIGATING: "bg-blue-500/20 text-blue-400 border border-blue-500/30",
  RESOLVED:      "bg-green-500/20 text-green-400 border border-green-500/30",
  FALSE_ALARM:   "bg-slate-500/20 text-slate-400 border border-slate-500/30",
};

export default function StatusBadge({ status }: { status: IncidentStatus }) {
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${map[status]}`}>
      {status.replace("_", " ")}
    </span>
  );
}
