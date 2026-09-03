import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "react-query";
import {
  ArrowLeft,
  Play,
  Clock,
  Server,
  Activity,
  FileText,
  ShieldAlert,
  ListChecks,
  Search,
} from "lucide-react";
import { incidentsApi } from "../api/incidents";
import SeverityBadge from "../components/SeverityBadge";
import StatusBadge from "../components/StatusBadge";
import RootCauseCard from "../components/RootCauseCard";
import CausalTimeline from "../components/CausalTimeline";
import HypothesisMatrix from "../components/HypothesisMatrix";
import RecommendedActions from "../components/RecommendedActions";
import EvidenceExplorer from "../components/EvidenceExplorer";
import MetricsChart from "../components/MetricsChart";

type Tab = "overview" | "timeline" | "metrics" | "hypotheses" | "evidence" | "actions";

export default function InvestigationPage() {
  const { incidentId } = useParams<{ incidentId: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  const { data: incident } = useQuery(
    ["incident", incidentId],
    () => incidentsApi.get(incidentId!),
    { enabled: !!incidentId }
  );

  const { data: investigation, isLoading: invLoading } = useQuery(
    ["investigation", incidentId],
    () => incidentsApi.getInvestigation(incidentId!),
    { enabled: !!incidentId, retry: false }
  );

  const { data: evidenceData } = useQuery(
    ["evidence", incidentId],
    () => incidentsApi.getEvidence(incidentId!),
    { enabled: !!incidentId && !!investigation, retry: false }
  );

  const { data: timelineData } = useQuery(
    ["timeline", incidentId],
    () => incidentsApi.getTimeline(incidentId!),
    { enabled: !!incidentId && !!investigation, retry: false }
  );

  const investigateMutation = useMutation(
    () => incidentsApi.triggerInvestigation(incidentId!),
    {
      onSuccess: () => {
        qc.invalidateQueries(["investigation", incidentId]);
        qc.invalidateQueries(["evidence", incidentId]);
        qc.invalidateQueries(["timeline", incidentId]);
        qc.invalidateQueries(["incident", incidentId]);
        qc.invalidateQueries("incidents");
      },
    }
  );

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "overview",   label: "Overview",      icon: <ShieldAlert size={14} /> },
    { id: "timeline",   label: "Timeline",      icon: <Clock size={14} /> },
    { id: "metrics",    label: "Metrics",       icon: <Activity size={14} /> },
    { id: "hypotheses", label: "Hypotheses",    icon: <Search size={14} /> },
    { id: "evidence",   label: "Evidence",      icon: <FileText size={14} /> },
    { id: "actions",    label: "Actions",       icon: <ListChecks size={14} /> },
  ];

  if (!incident) {
    return (
      <div className="p-6 text-slate-400">Loading incident...</div>
    );
  }

  const timeline = timelineData?.timeline ?? [];
  const evidence = evidenceData?.evidence_package;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Back nav */}
      <button
        onClick={() => navigate("/dashboard")}
        className="flex items-center gap-2 text-slate-400 hover:text-white text-sm mb-6 transition-colors"
      >
        <ArrowLeft size={16} /> Back to Dashboard
      </button>

      {/* Incident header */}
      <div className="bg-[#0f1629] border border-[#1e2a45] rounded-xl p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-blue-400 font-mono font-bold text-lg">{incident.incident_id}</span>
              <SeverityBadge severity={incident.severity} />
              <StatusBadge status={incident.status} />
            </div>
            <div className="flex items-center gap-2 text-slate-400 text-sm">
              <Server size={14} />
              <span>{incident.service}</span>
              <span className="mx-2 text-slate-600">•</span>
              <Clock size={14} />
              <span>{new Date(incident.start_time).toLocaleString()}</span>
            </div>
            {incident.description && (
              <p className="text-slate-300 text-sm mt-2">{incident.description}</p>
            )}
          </div>

          {!investigation ? (
            <button
              onClick={() => investigateMutation.mutate()}
              disabled={investigateMutation.isLoading}
              className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-white text-sm font-semibold transition-colors"
            >
              <Play size={15} />
              {investigateMutation.isLoading ? "Investigating..." : "Run AI Investigation"}
            </button>
          ) : (
            <button
              onClick={() => investigateMutation.mutate()}
              disabled={investigateMutation.isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-[#1e2a45] hover:bg-[#253352] rounded-lg text-slate-300 text-sm transition-colors"
            >
              <Play size={14} />
              {investigateMutation.isLoading ? "Re-investigating..." : "Re-investigate"}
            </button>
          )}
        </div>
      </div>

      {/* Investigation result */}
      {investigation && (
        <>
          {/* Tabs */}
          <div className="flex gap-1 mb-6 bg-[#0f1629] border border-[#1e2a45] rounded-xl p-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors flex-1 justify-center
                  ${activeTab === tab.id
                    ? "bg-blue-600 text-white"
                    : "text-slate-400 hover:text-white hover:bg-[#1e2a45]"
                  }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div>
            {/* Overview */}
            {activeTab === "overview" && (
              <div className="space-y-6">
                <RootCauseCard
                  investigation={investigation}
                  onViewEvidence={() => setActiveTab("evidence")}
                  onViewHypotheses={() => setActiveTab("hypotheses")}
                />

                {/* Quick timeline preview */}
                {timeline.length > 0 && (
                  <div className="bg-[#0f1629] border border-[#1e2a45] rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-300 mb-4">Causal Timeline</h3>
                    <CausalTimeline events={timeline.slice(0, 8)} />
                    {timeline.length > 8 && (
                      <button
                        onClick={() => setActiveTab("timeline")}
                        className="mt-3 text-blue-400 text-xs hover:underline"
                      >
                        View full timeline ({timeline.length} events)
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Timeline */}
            {activeTab === "timeline" && (
              <div className="bg-[#0f1629] border border-[#1e2a45] rounded-xl p-6">
                <h3 className="text-sm font-semibold text-slate-300 mb-5">Full Causal Timeline</h3>
                <CausalTimeline events={timeline} />
              </div>
            )}

            {/* Metrics */}
            {activeTab === "metrics" && (
              <div className="space-y-4">
                {["error_rate", "latency_p95", "db_connections", "cpu_usage"].map((metric) => {
                  const hasData = timeline.some(
                    (e: { type: string; metric_name?: string }) => e.type === "metric" && e.metric_name === metric
                  );
                  if (!hasData) return null;
                  const colors: Record<string, string> = {
                    error_rate:    "#ef4444",
                    latency_p95:   "#f97316",
                    db_connections:"#3b82f6",
                    cpu_usage:     "#a855f7",
                  };
                  return (
                    <div key={metric} className="bg-[#0f1629] border border-[#1e2a45] rounded-xl p-5">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                        {metric.replace(/_/g, " ")}
                      </h4>
                      <MetricsChart
                        events={timeline}
                        metricName={metric}
                        color={colors[metric]}
                        incidentStart={incident.start_time}
                      />
                    </div>
                  );
                })}
              </div>
            )}

            {/* Hypotheses */}
            {activeTab === "hypotheses" && (
              <div className="bg-[#0f1629] border border-[#1e2a45] rounded-xl p-6">
                <h3 className="text-sm font-semibold text-slate-300 mb-5">Hypothesis Evaluation</h3>
                <HypothesisMatrix hypotheses={investigation.hypotheses ?? []} />
              </div>
            )}

            {/* Evidence */}
            {activeTab === "evidence" && evidence && (
              <div className="bg-[#0f1629] border border-[#1e2a45] rounded-xl p-6">
                <h3 className="text-sm font-semibold text-slate-300 mb-5">Evidence Explorer</h3>
                <EvidenceExplorer evidence={evidence} />
              </div>
            )}

            {/* Actions */}
            {activeTab === "actions" && (
              <div className="bg-[#0f1629] border border-[#1e2a45] rounded-xl p-6">
                <div className="flex items-start justify-between mb-5">
                  <h3 className="text-sm font-semibold text-slate-300">Recommended Actions</h3>
                  <div className="text-xs text-slate-500 italic border border-[#1e2a45] rounded px-2 py-1">
                    ⚠ AI recommends — engineer decides
                  </div>
                </div>
                <RecommendedActions actions={investigation.recommended_actions ?? []} />
              </div>
            )}
          </div>
        </>
      )}

      {/* No investigation yet */}
      {!investigation && !invLoading && (
        <div className="bg-[#0f1629] border border-[#1e2a45] rounded-xl p-12 text-center">
          <ShieldAlert size={40} className="text-slate-600 mx-auto mb-4" />
          <p className="text-slate-300 text-lg font-semibold mb-2">No investigation yet</p>
          <p className="text-slate-500 text-sm mb-6">
            Run the AI investigation to get root-cause analysis, hypotheses, and recommendations.
          </p>
          <button
            onClick={() => investigateMutation.mutate()}
            disabled={investigateMutation.isLoading}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-white font-semibold transition-colors"
          >
            {investigateMutation.isLoading ? "Investigating…" : "Run AI Investigation"}
          </button>
        </div>
      )}

      {investigateMutation.isError && (
        <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          Investigation failed. Make sure the backend is running and try again.
        </div>
      )}
    </div>
  );
}
