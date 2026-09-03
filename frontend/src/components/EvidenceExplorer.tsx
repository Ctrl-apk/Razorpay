import type { EvidencePackage } from "../types";
import { Rocket, Activity, FileText } from "lucide-react";

interface Props {
  evidence: EvidencePackage;
}

export default function EvidenceExplorer({ evidence }: Props) {
  return (
    <div className="space-y-6">
      {/* Deployments */}
      {evidence.deployments.length > 0 && (
        <div>
          <h4 className="flex items-center gap-2 text-xs font-bold text-purple-400 uppercase tracking-wider mb-3">
            <Rocket size={12} /> Deployments in Window
          </h4>
          <div className="space-y-2">
            {evidence.deployments.map((d, i) => (
              <div key={i} className="rounded-lg bg-purple-500/5 border border-purple-500/20 p-3">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-purple-300 font-mono font-semibold">{d.version}</span>
                    {d.commit_sha && (
                      <span className="text-slate-500 font-mono text-xs ml-3">{d.commit_sha.slice(0, 10)}</span>
                    )}
                    {d.author && <span className="text-slate-400 text-xs ml-3">by {d.author}</span>}
                  </div>
                  <span className="text-xs text-slate-400">
                    {d.minutes_before_incident.toFixed(1)}m before incident
                  </span>
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {new Date(d.timestamp).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metric Anomalies */}
      {evidence.metric_anomalies.length > 0 && (
        <div>
          <h4 className="flex items-center gap-2 text-xs font-bold text-blue-400 uppercase tracking-wider mb-3">
            <Activity size={12} /> Metric Anomalies
          </h4>
          <div className="grid grid-cols-2 gap-2">
            {evidence.metric_anomalies.map((m, i) => (
              <div key={i} className="rounded-lg bg-blue-500/5 border border-blue-500/20 p-3">
                <div className="text-blue-300 text-xs font-semibold uppercase mb-1">{m.metric}</div>
                <div className="text-white font-mono font-bold">
                  avg: {m.average?.toFixed(2)}
                </div>
                <div className="text-slate-500 text-xs mt-1">{m.samples} samples</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error Logs */}
      {evidence.error_logs.length > 0 && (
        <div>
          <h4 className="flex items-center gap-2 text-xs font-bold text-yellow-400 uppercase tracking-wider mb-3">
            <FileText size={12} /> Error Logs
          </h4>
          <div className="space-y-1.5">
            {evidence.error_logs.map((l, i) => (
              <div key={i} className="flex gap-3 rounded bg-[#0a0e1a] border border-[#1e2a45] p-2.5 font-mono text-xs">
                <span className="text-slate-500 flex-shrink-0">
                  {new Date(l.timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false })}
                </span>
                <span className={`font-bold flex-shrink-0 ${l.level === "ERROR" ? "text-red-400" : "text-yellow-400"}`}>
                  {l.level}
                </span>
                <span className="text-slate-300">{l.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
