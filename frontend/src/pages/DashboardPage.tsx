import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  Play,
  RefreshCw,
  ChevronRight,
  FlaskConical,
} from "lucide-react";
import { incidentsApi } from "../api/incidents";
import { scenariosApi } from "../api/scenarios";
import type { Incident, Severity } from "../types";
import SeverityBadge from "../components/SeverityBadge";
import StatusBadge from "../components/StatusBadge";
import ConfidenceBar from "../components/ConfidenceBar";

// ── helpers ──────────────────────────────────────────────────────────────────

function timeAgo(ts: string) {
  const diff = Date.now() - new Date(ts).getTime();
  const secs = Math.floor(diff / 1000);
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

const SEV_ORDER: Record<Severity, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };

// ── scenario names → human labels ────────────────────────────────────────────

const SCENARIO_LABELS: Record<string, { title: string; hint: string }> = {
  deployment_regression: {
    title: "Deployment Regression",
    hint:  "DB connection pool exhaustion after deploy v2.8.1",
  },
  database_failure: {
    title: "Database Failure",
    hint:  "Database server becomes unreachable, no recent deploy",
  },
  traffic_spike: {
    title: "Traffic Spike",
    hint:  "6× traffic surge saturates CPU, errors increase",
  },
  dependency_failure: {
    title: "Dependency Failure",
    hint:  "Payment gateway latency causes checkout failures",
  },
};

// ── Load-scenario panel (shown only when DB is empty) ────────────────────────

function LoadScenarioPanel({ onLoaded }: { onLoaded: (incidentId: string) => void }) {
  const { data } = useQuery("scenarios", scenariosApi.list, { staleTime: Infinity });
  const scenarios = data?.scenarios ?? [];
  const [active, setActive] = useState<string | null>(null);

  const runMutation = useMutation(
    (name: string) => scenariosApi.run(name),
    {
      onSuccess: (res) => {
        setActive(null);
        onLoaded(res.incident_id);
      },
      onError: () => setActive(null),
    }
  );

  return (
    <div className="max-w-2xl mx-auto mt-16 text-center">
      {/* Explainer */}
      <div className="mb-8">
        <FlaskConical size={36} className="text-blue-400 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-white mb-2">No incidents yet</h2>
        <p className="text-slate-400 text-sm leading-relaxed max-w-md mx-auto">
          This dashboard shows real production incidents. To try the system, load one of the
          pre-built scenarios below. Each scenario seeds realistic telemetry (metrics, logs,
          deployments) into the database so you can see the full AI investigation flow.
        </p>
      </div>

      {/* Scenario cards */}
      <div className="grid grid-cols-2 gap-3 text-left">
        {scenarios.map((name) => {
          const meta = SCENARIO_LABELS[name] ?? { title: name, hint: "" };
          const isRunning = active === name;
          return (
            <div key={name} className="bg-[#0f1629] border border-[#1e2a45] hover:border-blue-500/40 rounded-xl p-4 transition-colors">
              <div className="font-semibold text-white text-sm mb-1">{meta.title}</div>
              <div className="text-slate-500 text-xs mb-4 leading-relaxed">{meta.hint}</div>
              <button
                onClick={() => { setActive(name); runMutation.mutate(name); }}
                disabled={runMutation.isLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-white text-xs font-semibold transition-colors"
              >
                <Play size={12} />
                {isRunning ? "Loading…" : "Load scenario"}
              </button>
            </div>
          );
        })}
      </div>

      <p className="mt-6 text-xs text-slate-600">
        Scenarios use deterministic fixture data — no real systems are contacted.
      </p>
    </div>
  );
}

// ── Main dashboard ────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: incidents = [], isLoading, refetch } = useQuery(
    "incidents",
    () => incidentsApi.list(),
    { refetchInterval: 20000 }
  );

  // Pre-fetch investigations for visible incidents (silent — no throw on 404)
  const [investigations, setInvestigations] = useState<
    Record<string, { root_cause?: string; confidence_score?: number } | null>
  >({});

  // Load investigations once when incident list arrives
  const loadedRef = useState<Set<string>>(() => new Set())[0];
  incidents.forEach((inc) => {
    if (!loadedRef.has(inc.incident_id)) {
      loadedRef.add(inc.incident_id);
      incidentsApi.getInvestigationSafe(inc.incident_id).then((inv) => {
        setInvestigations((prev) => ({ ...prev, [inc.incident_id]: inv }));
      });
    }
  });

  // Investigate inline from the list
  const investigateMutation = useMutation(
    (incidentId: string) => incidentsApi.triggerInvestigation(incidentId),
    {
      onSuccess: (_data, incidentId) => {
        loadedRef.delete(incidentId); // force re-fetch
        incidentsApi.getInvestigationSafe(incidentId).then((inv) => {
          setInvestigations((prev) => ({ ...prev, [incidentId]: inv }));
        });
        qc.invalidateQueries("incidents");
      },
    }
  );

  // Sort: unresolved first, then by severity, then newest
  const sorted = [...incidents].sort((a, b) => {
    const aResolved = a.status === "RESOLVED" ? 1 : 0;
    const bResolved = b.status === "RESOLVED" ? 1 : 0;
    if (aResolved !== bResolved) return aResolved - bResolved;
    const sevDiff = (SEV_ORDER[a.severity] ?? 4) - (SEV_ORDER[b.severity] ?? 4);
    if (sevDiff !== 0) return sevDiff;
    return new Date(b.start_time).getTime() - new Date(a.start_time).getTime();
  });

  // KPI counts
  const active   = incidents.filter((i) => i.status !== "RESOLVED").length;
  const critical = incidents.filter((i) => i.severity === "CRITICAL" && i.status !== "RESOLVED").length;
  const invCount = incidents.filter((i) => i.status === "INVESTIGATING").length;
  const resolved = incidents.filter((i) => i.status === "RESOLVED").length;

  return (
    <div className="p-6 max-w-6xl mx-auto">

      {/* ── Page header ── */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-white">Incident Dashboard</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            AI-powered root-cause analysis for production incidents
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-amber-400 bg-amber-400/10 border border-amber-400/20 px-2 py-1 rounded font-semibold">
            DEMO
          </span>
          <button
            onClick={() => { refetch(); loadedRef.clear(); }}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1e2a45] hover:bg-[#253352] rounded-lg text-slate-300 text-xs transition-colors"
          >
            <RefreshCw size={12} /> Refresh
          </button>
        </div>
      </div>

      {/* ── KPIs — only when there's data ── */}
      {incidents.length > 0 && (
        <div className="grid grid-cols-4 gap-3 mb-6">
          {[
            { label: "Active",        value: active,   color: active > 0   ? "text-red-400"    : "text-slate-400" },
            { label: "Critical",      value: critical, color: critical > 0 ? "text-red-400"    : "text-slate-400" },
            { label: "Investigating", value: invCount, color: invCount > 0 ? "text-blue-400"   : "text-slate-400" },
            { label: "Resolved",      value: resolved, color: "text-green-400" },
          ].map((k) => (
            <div key={k.label} className="bg-[#0f1629] border border-[#1e2a45] rounded-xl px-5 py-4">
              <div className={`text-3xl font-bold ${k.color}`}>{k.value}</div>
              <div className="text-xs text-slate-500 mt-1 font-semibold tracking-wide">{k.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* ── Loading ── */}
      {isLoading && (
        <div className="text-center py-20 text-slate-500 text-sm">Loading incidents…</div>
      )}

      {/* ── Empty state: load a scenario ── */}
      {!isLoading && incidents.length === 0 && (
        <LoadScenarioPanel
          onLoaded={(incidentId) => {
            refetch();
            navigate(`/incidents/${incidentId}`);
          }}
        />
      )}

      {/* ── Incident table ── */}
      {incidents.length > 0 && (
        <div className="bg-[#0f1629] border border-[#1e2a45] rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-5 py-3 border-b border-[#1e2a45]">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <AlertTriangle size={13} className="text-orange-400" />
              Incidents
            </span>
            <span className="text-xs text-slate-500">{incidents.length} total</span>
          </div>

          <table className="w-full">
            <thead>
              <tr className="text-xs text-slate-500 uppercase tracking-wider border-b border-[#1e2a45]">
                <th className="text-left px-5 py-3">Severity</th>
                <th className="text-left px-5 py-3">Service</th>
                <th className="text-left px-5 py-3">Description</th>
                <th className="text-left px-5 py-3">Status</th>
                <th className="text-left px-5 py-3 w-40">AI Confidence</th>
                <th className="text-left px-5 py-3">Root Cause</th>
                <th className="text-right px-5 py-3">Started</th>
                <th className="px-4 py-3 w-8" />
              </tr>
            </thead>
            <tbody>
              {sorted.map((inc: Incident) => {
                const inv = investigations[inc.incident_id];
                const hasInv = inv != null;
                const isInvestigating = investigateMutation.variables === inc.incident_id && investigateMutation.isLoading;

                return (
                  <tr
                    key={inc.id}
                    className="border-b border-[#1e2a45] hover:bg-[#151d35] transition-colors"
                  >
                    {/* Severity */}
                    <td className="px-5 py-4">
                      <SeverityBadge severity={inc.severity} />
                    </td>

                    {/* Service */}
                    <td className="px-5 py-4">
                      <div className="text-white text-sm font-semibold">{inc.service}</div>
                      <div className="text-slate-600 font-mono text-xs">{inc.incident_id}</div>
                    </td>

                    {/* Description */}
                    <td className="px-5 py-4 max-w-[220px]">
                      <div className="text-slate-300 text-sm truncate">{inc.description ?? "—"}</div>
                    </td>

                    {/* Status */}
                    <td className="px-5 py-4">
                      <StatusBadge status={inc.status} />
                    </td>

                    {/* AI Confidence */}
                    <td className="px-5 py-4 w-40">
                      {hasInv && inv?.confidence_score != null ? (
                        <ConfidenceBar score={inv.confidence_score} />
                      ) : (
                        <button
                          onClick={(e) => { e.stopPropagation(); investigateMutation.mutate(inc.incident_id); }}
                          disabled={isInvestigating}
                          className="flex items-center gap-1.5 px-2.5 py-1 bg-blue-600/20 hover:bg-blue-600/40 border border-blue-500/30 rounded text-blue-300 text-xs transition-colors disabled:opacity-50"
                        >
                          <Play size={10} />
                          {isInvestigating ? "Running…" : "Investigate"}
                        </button>
                      )}
                    </td>

                    {/* Root Cause */}
                    <td className="px-5 py-4 max-w-[240px]">
                      {hasInv && inv?.root_cause ? (
                        <span className="text-blue-300 text-xs">{inv.root_cause}</span>
                      ) : (
                        <span className="text-slate-600 text-xs italic">—</span>
                      )}
                    </td>

                    {/* Started */}
                    <td className="px-5 py-4 text-right">
                      <span className="text-slate-400 text-xs">{timeAgo(inc.start_time)}</span>
                    </td>

                    {/* Open */}
                    <td className="px-4 py-4">
                      <button
                        onClick={() => navigate(`/incidents/${inc.incident_id}`)}
                        className="flex items-center gap-1 px-2.5 py-1 bg-[#1e2a45] hover:bg-[#253352] rounded text-slate-300 text-xs transition-colors"
                        title="Open investigation"
                      >
                        Open <ChevronRight size={12} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Load another scenario link ── */}
      {incidents.length > 0 && (
        <div className="mt-4 flex items-center gap-3">
          <span className="text-xs text-slate-500">Want to try a different scenario?</span>
          <button
            onClick={() => navigate("/scenarios")}
            className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            <FlaskConical size={12} /> Load another scenario
          </button>
          {investigateMutation.isError && (
            <span className="text-xs text-red-400 ml-auto">
              Investigation failed — make sure the backend is running.
            </span>
          )}
        </div>
      )}
    </div>
  );
}
