import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "react-query";
import {
  Play,
  CheckCircle2,
  Info,
  ExternalLink,
  ArrowRight,
  Database,
  GitBranch,
  Activity,
  FileText,
  Cpu,
  Zap,
} from "lucide-react";
import { scenariosApi } from "../api/scenarios";

// ── scenario fixture metadata ─────────────────────────────────────────────────

const SCENARIO_META: Record<string, {
  title: string;
  service: string;
  what: string;
  rootCause: string;
  events: string[];
  severityColor: string;
}> = {
  deployment_regression: {
    title:         "Deployment Regression",
    service:       "payments-api",
    what:          "API errors spike 2 minutes after deploying v2.8.1",
    rootCause:     "Database connection pool exhaustion",
    severityColor: "border-orange-500/30",
    events: [
      "02:07 — Deployment v2.8.1 pushed to production",
      "02:09 — DB connections spike 42 → 98",
      "02:09 — \"connection timeout\" errors in logs",
      "02:10 — API error rate 0.4% → 8.7%",
      "02:10 — Incident detected",
    ],
  },
  database_failure: {
    title:         "Database Failure",
    service:       "orders-api",
    what:          "Database server becomes unreachable — no recent deployment",
    rootCause:     "Database server failure (infrastructure)",
    severityColor: "border-red-500/30",
    events: [
      "14:22 — DB connections drop to zero",
      "14:22 — \"connection refused\" in logs",
      "14:22 — Health check: database unreachable",
      "14:23 — API error rate spikes to 12.5%",
      "14:23 — Circuit breaker opens",
    ],
  },
  traffic_spike: {
    title:         "Traffic Spike",
    service:       "storefront-api",
    what:          "Sudden 6× traffic surge saturates CPU and worker threads",
    rootCause:     "Resource saturation from traffic surge",
    severityColor: "border-yellow-500/30",
    events: [
      "18:30 — Requests/sec 420 → 2640",
      "18:31 — CPU 25% → 91%",
      "18:31 — Worker thread pool saturated",
      "18:31 — Error rate increases to 5.3%",
      "18:32 — Auto-scaling triggered",
    ],
  },
  dependency_failure: {
    title:         "Dependency Failure",
    service:       "checkout-api",
    what:          "External payment gateway latency causes checkout failures",
    rootCause:     "External payment gateway outage",
    severityColor: "border-purple-500/30",
    events: [
      "09:18 — Payment gateway: 3200ms (threshold 1000ms)",
      "09:18 — Gateway request timeouts begin",
      "09:19 — Checkout failures cascade",
      "09:19 — Circuit breaker opens on payment-gateway",
      "09:20 — All checkout requests failing",
    ],
  },
};

// ── Real integration endpoints shown to judges ────────────────────────────────

const REAL_ENDPOINTS = [
  {
    icon:    <Activity size={14} className="text-blue-400" />,
    source:  "Prometheus / Grafana",
    label:   "POST /api/v1/telemetry/metrics",
    example: `{ "service": "payments-api", "metric_name": "error_rate", "value": 8.7, "timestamp": "..." }`,
  },
  {
    icon:    <FileText size={14} className="text-yellow-400" />,
    source:  "Loki / ELK / Datadog",
    label:   "POST /api/v1/telemetry/logs",
    example: `{ "service": "payments-api", "level": "ERROR", "message": "connection timeout", "timestamp": "..." }`,
  },
  {
    icon:    <Cpu size={14} className="text-purple-400" />,
    source:  "Jaeger / Zipkin",
    label:   "POST /api/v1/telemetry/traces",
    example: `{ "service": "payments-api", "operation": "db.query", "duration_ms": 5200, "status": "error", "timestamp": "..." }`,
  },
  {
    icon:    <GitBranch size={14} className="text-green-400" />,
    source:  "GitHub Webhooks / CI/CD",
    label:   "POST /api/v1/telemetry/deployments",
    example: `{ "service": "payments-api", "version": "v2.8.1", "commit_sha": "abc123", "timestamp": "..." }`,
  },
];

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ScenariosPage() {
  const navigate = useNavigate();
  const [active, setActive]   = useState<string | null>(null);
  const [loaded, setLoaded]   = useState<{ name: string; incidentId: string } | null>(null);
  const [showEndpoint, setShowEndpoint] = useState<number | null>(null);

  const { data } = useQuery("scenarios", scenariosApi.list, { staleTime: Infinity });
  const scenarios = data?.scenarios ?? [];

  const runMutation = useMutation(
    (name: string) => scenariosApi.run(name),
    {
      onSuccess: (res, name) => {
        setActive(null);
        setLoaded({ name, incidentId: res.incident_id });
      },
      onError: () => setActive(null),
    }
  );

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-8">

      {/* ── Page header ── */}
      <div>
        <h1 className="text-xl font-bold text-white">Load Demo Incident</h1>
        <p className="text-slate-400 text-sm mt-1">
          Try the AI investigation pipeline with pre-built realistic telemetry data.
        </p>
      </div>

      {/* ── HOW IT WORKS — the core explainer ── */}
      <div className="rounded-xl border border-blue-500/20 bg-[#0d1527] p-5">
        <div className="flex items-center gap-2 mb-4">
          <Zap size={15} className="text-blue-400" />
          <span className="text-sm font-bold text-white">How the system works with real data</span>
        </div>

        {/* Flow diagram */}
        <div className="flex items-center gap-2 flex-wrap mb-5">
          {["Prometheus", "Loki / ELK", "Jaeger", "GitHub Webhooks"].map((s, i, arr) => (
            <span key={s} className="flex items-center gap-2">
              <span className="text-xs px-2.5 py-1 rounded-full bg-[#1e2a45] text-slate-300 border border-[#253352]">
                {s}
              </span>
              {i < arr.length - 1 && <span className="text-slate-600 text-xs">+</span>}
            </span>
          ))}
          <ArrowRight size={14} className="text-slate-500 mx-1" />
          <span className="text-xs px-2.5 py-1 rounded-full bg-blue-600/20 text-blue-300 border border-blue-500/30 font-semibold">
            AI Incident Investigator
          </span>
          <ArrowRight size={14} className="text-slate-500 mx-1" />
          {["Root Cause", "Evidence", "Hypotheses", "Actions"].map((o) => (
            <span key={o} className="text-xs px-2.5 py-1 rounded-full bg-green-500/10 text-green-300 border border-green-500/20">
              {o}
            </span>
          ))}
        </div>

        <p className="text-slate-400 text-sm mb-5">
          In production, your observability tools send telemetry to four REST endpoints below.
          The investigation pipeline is identical whether the data comes from a real Prometheus
          scrape or from the demo fixtures — the AI only ever sees the normalized JSON.
        </p>

        {/* Real integration endpoints */}
        <div className="space-y-2">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
            Real integration endpoints — your tools send data here:
          </div>
          {REAL_ENDPOINTS.map((ep, i) => (
            <div key={i} className="rounded-lg border border-[#1e2a45] bg-[#0a0e1a] overflow-hidden">
              <button
                onClick={() => setShowEndpoint(showEndpoint === i ? null : i)}
                className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-[#0f1629] transition-colors text-left"
              >
                {ep.icon}
                <span className="text-xs font-mono text-green-300 flex-1">{ep.label}</span>
                <span className="text-xs text-slate-500">{ep.source}</span>
                <span className="text-slate-600 text-xs ml-2">{showEndpoint === i ? "▲" : "▼"}</span>
              </button>
              {showEndpoint === i && (
                <div className="px-4 pb-3 border-t border-[#1e2a45]">
                  <div className="text-xs text-slate-500 mb-1 mt-2">Example payload:</div>
                  <code className="block text-xs text-slate-300 font-mono bg-[#050810] rounded p-2 leading-relaxed whitespace-pre-wrap">
                    {ep.example}
                  </code>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-4 flex items-center gap-3">
          <a
            href="http://localhost:8000/api/docs"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            <ExternalLink size={12} /> Open full API docs (Swagger UI)
          </a>
          <span className="text-slate-600 text-xs">·</span>
          <span className="text-xs text-slate-500">
            All endpoints accept standard JSON — no proprietary SDK needed
          </span>
        </div>
      </div>

      {/* ── Demo fixtures explainer ── */}
      <div className="flex gap-3 bg-amber-500/5 border border-amber-500/20 rounded-xl p-4 text-sm text-slate-300">
        <Info size={15} className="text-amber-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="text-white font-semibold">What the demo scenarios actually do: </span>
          <span className="text-slate-400">
            Each scenario calls the same four endpoints above with pre-built JSON payloads —
            realistic metrics, log lines, and deployment records. The AI investigation then runs
            on that data exactly as it would on real production telemetry.
            Nothing is hard-coded into the investigation logic itself.
          </span>
        </div>
      </div>

      {/* ── Success banner ── */}
      {loaded && (
        <div className="flex items-center justify-between bg-green-500/10 border border-green-500/30 rounded-xl p-4">
          <div className="flex items-center gap-3">
            <CheckCircle2 size={18} className="text-green-400" />
            <div>
              <div className="text-green-300 font-semibold text-sm">
                {SCENARIO_META[loaded.name]?.title ?? loaded.name} loaded
              </div>
              <div className="text-slate-400 text-xs">
                Incident {loaded.incidentId} is ready — open the investigation to see the AI analysis.
              </div>
            </div>
          </div>
          <button
            onClick={() => navigate(`/incidents/${loaded.incidentId}`)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm font-semibold transition-colors"
          >
            Open Investigation →
          </button>
        </div>
      )}

      {/* ── Scenario cards ── */}
      <div>
        <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
          Available demo scenarios
        </div>
        <div className="grid grid-cols-2 gap-4">
          {scenarios.map((name) => {
            const m = SCENARIO_META[name];
            if (!m) return null;
            const isRunning = active === name;

            return (
              <div
                key={name}
                className={`bg-[#0f1629] border ${m.severityColor} rounded-xl p-5`}
              >
                {/* Title + service */}
                <div className="flex items-start justify-between mb-1">
                  <span className="text-white font-bold text-sm">{m.title}</span>
                  <span className="text-xs text-slate-500 font-mono bg-[#0a0e1a] px-2 py-0.5 rounded">
                    {m.service}
                  </span>
                </div>

                <p className="text-slate-400 text-xs mb-3">{m.what}</p>

                {/* Event timeline */}
                <div className="mb-3 space-y-0.5">
                  {m.events.map((e, i) => (
                    <div key={i} className="text-xs text-slate-500 font-mono leading-snug">
                      {e}
                    </div>
                  ))}
                </div>

                {/* Data that will be seeded */}
                <div className="flex gap-2 flex-wrap mb-4">
                  {[
                    { icon: <Activity size={10} />,   label: "Metrics" },
                    { icon: <FileText size={10} />,   label: "Logs"    },
                    { icon: <GitBranch size={10} />,  label: name === "deployment_regression" ? "1 Deployment" : "No deployment" },
                    { icon: <Database size={10} />,   label: "DB events" },
                  ].map((tag) => (
                    <span key={tag.label} className="flex items-center gap-1 text-xs text-slate-500 bg-[#0a0e1a] px-2 py-0.5 rounded border border-[#1e2a45]">
                      {tag.icon} {tag.label}
                    </span>
                  ))}
                </div>

                {/* Expected root cause */}
                <div className="flex items-center gap-2 mb-4 text-xs">
                  <span className="text-slate-500">AI will identify:</span>
                  <span className="text-yellow-300 font-semibold">{m.rootCause}</span>
                </div>

                <button
                  onClick={() => { setActive(name); setLoaded(null); runMutation.mutate(name); }}
                  disabled={runMutation.isLoading}
                  className="w-full flex items-center justify-center gap-2 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-white text-sm font-semibold transition-colors"
                >
                  <Play size={13} />
                  {isRunning ? "Loading…" : "Load scenario"}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {scenarios.length === 0 && (
        <div className="text-center py-16 text-slate-500 text-sm">
          Cannot reach the backend. Make sure it is running on port 8000.
        </div>
      )}
    </div>
  );
}
