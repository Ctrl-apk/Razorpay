import type { Severity } from "../types";

const map: Record<Severity, string> = {
  CRITICAL: "bg-red-500/20 text-red-400 border border-red-500/30",
  HIGH:     "bg-orange-500/20 text-orange-400 border border-orange-500/30",
  MEDIUM:   "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
  LOW:      "bg-blue-500/20 text-blue-400 border border-blue-500/30",
};

export default function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${map[severity]}`}>
      {severity}
    </span>
  );
}
