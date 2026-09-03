import { Rocket, Activity, FileText, AlertTriangle } from "lucide-react";
import type { TimelineEvent } from "../types";

interface Props {
  events: TimelineEvent[];
}

function fmt(ts: string) {
  const d = new Date(ts);
  return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
}

function EventIcon({ type }: { type: TimelineEvent["type"] }) {
  switch (type) {
    case "deployment":    return <Rocket size={14} className="text-purple-400" />;
    case "metric":        return <Activity size={14} className="text-blue-400" />;
    case "log":           return <FileText size={14} className="text-yellow-400" />;
    case "incident_start": return <AlertTriangle size={14} className="text-red-400" />;
    default:              return <Activity size={14} className="text-slate-400" />;
  }
}

function EventLabel(event: TimelineEvent) {
  switch (event.type) {
    case "deployment":
      return (
        <span>
          <span className="text-purple-300 font-semibold">Deployment</span>{" "}
          <span className="text-white">{event.version}</span>
          {event.commit_sha && (
            <span className="text-slate-500 ml-2 font-mono text-xs">{event.commit_sha.slice(0, 8)}</span>
          )}
        </span>
      );
    case "metric":
      return (
        <span>
          <span className="text-blue-300">{event.metric_name}</span>
          {" → "}
          <span className="text-white font-mono">{event.value?.toFixed(1)}</span>
          {event.unit && <span className="text-slate-400 ml-1">{event.unit}</span>}
        </span>
      );
    case "log":
      return (
        <span>
          <span className={`font-semibold mr-2 ${event.level === "ERROR" ? "text-red-400" : "text-yellow-400"}`}>
            {event.level}
          </span>
          <span className="text-slate-300">{event.message}</span>
        </span>
      );
    case "incident_start":
      return <span className="text-red-400 font-bold">⚡ Incident Detected</span>;
    default:
      return <span className="text-slate-400">Unknown event</span>;
  }
}

export default function CausalTimeline({ events }: Props) {
  if (!events || events.length === 0) {
    return (
      <div className="text-slate-500 text-sm text-center py-8">
        No timeline events available
      </div>
    );
  }

  // Deduplicate metrics — show one per metric_name per minute
  const seen = new Set<string>();
  const filtered = events.filter((e) => {
    if (e.type !== "metric") return true;
    const key = `${e.metric_name}:${e.timestamp.slice(0, 16)}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  return (
    <div className="space-y-0">
      {filtered.map((event, idx) => (
        <div key={idx} className="flex gap-3">
          {/* Time column */}
          <div className="w-20 flex-shrink-0 text-xs text-slate-500 pt-3 text-right font-mono">
            {fmt(event.timestamp)}
          </div>

          {/* Line + dot */}
          <div className="flex flex-col items-center">
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-1.5
                ${event.type === "incident_start" ? "bg-red-500/20 border border-red-500/50" :
                  event.type === "deployment"     ? "bg-purple-500/20 border border-purple-500/50" :
                  event.type === "log"            ? "bg-yellow-500/20 border border-yellow-500/30" :
                  "bg-blue-500/20 border border-blue-500/30"}`}
            >
              <EventIcon type={event.type} />
            </div>
            {idx < filtered.length - 1 && (
              <div className="w-px flex-1 bg-[#1e2a45] my-1" />
            )}
          </div>

          {/* Content */}
          <div className="flex-1 pb-4 pt-2.5 text-sm">
            {EventLabel(event)}
          </div>
        </div>
      ))}
    </div>
  );
}
