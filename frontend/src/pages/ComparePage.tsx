import { ArrowDown, Zap } from "lucide-react";

function WithoutAI() {
  const steps = [
    { tool: "Grafana",        action: "See error rate spike",         time: "2 min",  color: "text-orange-400" },
    { tool: "Prometheus",     action: "Check metrics manually",       time: "5 min",  color: "text-orange-400" },
    { tool: "Kibana / Logs",  action: "Grep for error messages",      time: "8 min",  color: "text-orange-400" },
    { tool: "GitHub",         action: "Check recent deployments",     time: "4 min",  color: "text-orange-400" },
    { tool: "Jaeger",         action: "Trace individual requests",    time: "10 min", color: "text-orange-400" },
    { tool: "Manual",         action: "Correlate all observations",   time: "15 min", color: "text-red-400" },
    { tool: "Hypothesis",     action: "Guess possible causes",        time: "10 min", color: "text-red-400" },
    { tool: "Investigation",  action: "Test each hypothesis manually","time": "20 min", color: "text-red-400" },
  ];

  const total = "74+ min";

  return (
    <div className="bg-[#0f1629] border border-red-500/20 rounded-xl p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-8 h-8 bg-red-500/20 rounded-lg flex items-center justify-center">
          <span className="text-red-400 font-bold text-sm">✗</span>
        </div>
        <div>
          <h2 className="text-white font-bold">Without AI Incident Investigator</h2>
          <p className="text-slate-400 text-xs">Today's manual investigation process</p>
        </div>
      </div>

      <div className="space-y-2">
        {steps.map((step, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="w-5 h-5 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center flex-shrink-0">
              <span className="text-red-400 text-xs">{i + 1}</span>
            </div>
            <div className="flex-1 flex items-center justify-between bg-[#0a0e1a] rounded-lg px-3 py-2">
              <div>
                <span className={`font-semibold text-sm ${step.color}`}>{step.tool}</span>
                <span className="text-slate-400 text-sm"> — {step.action}</span>
              </div>
              <span className="text-red-400/70 text-xs font-mono">{step.time}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center justify-between">
        <span className="text-red-300 font-semibold text-sm">Total investigation time</span>
        <span className="text-red-400 font-bold text-xl font-mono">{total}</span>
      </div>

      <p className="text-slate-500 text-xs mt-3 italic">
        Context switching between 5+ tools. Each transition adds cognitive overhead and delays root cause identification.
      </p>
    </div>
  );
}

function WithAI() {
  const steps = [
    { phase: "Telemetry Ingestion",    action: "Metrics, logs, traces, deployments collected",   time: "auto",   color: "text-blue-400" },
    { phase: "Temporal Correlation",   action: "Events correlated across time window",            time: "auto",   color: "text-blue-400" },
    { phase: "Evidence Extraction",    action: "Relevant evidence package compiled",              time: "auto",   color: "text-cyan-400" },
    { phase: "Hypothesis Evaluation",  action: "4+ competing hypotheses evaluated",               time: "auto",   color: "text-cyan-400" },
    { phase: "Root Cause",             action: "Most likely cause identified with confidence",    time: "auto",   color: "text-green-400" },
    { phase: "Evidence Chain",         action: "Full evidence chain shown to engineer",           time: "auto",   color: "text-green-400" },
    { phase: "Recommended Action",     action: "Specific investigation steps generated",          time: "auto",   color: "text-green-400" },
    { phase: "Engineer Decision",      action: "Engineer reviews and acts on recommendation",     time: "< 5 min", color: "text-white" },
  ];

  return (
    <div className="bg-[#0f1629] border border-green-500/20 rounded-xl p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-8 h-8 bg-green-500/20 rounded-lg flex items-center justify-center">
          <Zap size={16} className="text-green-400" />
        </div>
        <div>
          <h2 className="text-white font-bold">With AI Incident Investigator</h2>
          <p className="text-slate-400 text-xs">Automatic evidence-grounded causal investigation</p>
        </div>
      </div>

      <div className="space-y-2">
        {steps.map((step, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="w-5 h-5 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0">
              <span className="text-blue-400 text-xs">{i + 1}</span>
            </div>
            <div className="flex-1 flex items-center justify-between bg-[#0a0e1a] rounded-lg px-3 py-2">
              <div>
                <span className={`font-semibold text-sm ${step.color}`}>{step.phase}</span>
                <span className="text-slate-400 text-sm"> — {step.action}</span>
              </div>
              <span className={`text-xs font-mono ${step.time === "auto" ? "text-blue-400/70" : "text-green-400"}`}>
                {step.time}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 p-3 bg-green-500/10 border border-green-500/30 rounded-lg flex items-center justify-between">
        <span className="text-green-300 font-semibold text-sm">Total investigation time</span>
        <span className="text-green-400 font-bold text-xl font-mono">{"< 10 min"}</span>
      </div>

      <p className="text-slate-500 text-xs mt-3 italic">
        Engineer stays in one interface. AI handles correlation, hypothesis evaluation, and evidence linking automatically.
      </p>
    </div>
  );
}

export default function ComparePage() {
  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-white mb-3">Why AI Incident Investigator?</h1>
        <p className="text-slate-400 max-w-2xl mx-auto">
          Observability tools tell you <span className="text-white font-semibold">what</span> is broken.
          AI Incident Investigator tells you <span className="text-blue-400 font-semibold">why</span> it broke
          and <span className="text-green-400 font-semibold">what to do next</span>.
        </p>
      </div>

      {/* Core value prop */}
      <div className="grid grid-cols-3 gap-4 mb-10">
        {[
          { title: "Grafana", role: "Shows WHAT is happening", icon: "📊", desc: "Dashboards, charts, alerts" },
          { title: "GitHub",  role: "Shows WHAT changed",      icon: "🔀", desc: "Deployments, commits, diffs" },
          { title: "Logs",    role: "Shows WHAT failed",       icon: "📋", desc: "Error messages, stack traces" },
        ].map((item) => (
          <div key={item.title} className="bg-[#0f1629] border border-[#1e2a45] rounded-xl p-4 text-center">
            <div className="text-3xl mb-2">{item.icon}</div>
            <div className="text-white font-bold">{item.title}</div>
            <div className="text-slate-400 text-xs mt-1">{item.role}</div>
            <div className="text-slate-500 text-xs mt-1">{item.desc}</div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-center gap-4 mb-10">
        <div className="flex-1 h-px bg-[#1e2a45]" />
        <div className="flex items-center gap-2 bg-blue-600 px-5 py-3 rounded-xl">
          <ArrowDown size={18} className="text-white" />
          <span className="text-white font-bold">AI Incident Investigator connects the dots</span>
          <ArrowDown size={18} className="text-white" />
        </div>
        <div className="flex-1 h-px bg-[#1e2a45]" />
      </div>

      {/* Side-by-side comparison */}
      <div className="grid grid-cols-2 gap-6 mb-10">
        <WithoutAI />
        <WithAI />
      </div>

      {/* Key differentiator */}
      <div className="bg-gradient-to-br from-blue-900/30 to-[#0f1629] border border-blue-500/30 rounded-xl p-8 text-center">
        <h2 className="text-xl font-bold text-white mb-4">The Core Differentiator</h2>
        <div className="grid grid-cols-3 gap-6">
          {[
            { label: "Evidence-Grounded",   desc: "Every conclusion is backed by actual telemetry. No hallucinated metrics.",     icon: "🔬" },
            { label: "Hypothesis Evaluated", desc: "4+ competing explanations considered and ranked by evidence strength.",        icon: "⚖️" },
            { label: "Engineer Controls",   desc: "AI recommends. Human decides. No automated production changes.",               icon: "🎯" },
          ].map((item) => (
            <div key={item.label} className="text-center">
              <div className="text-4xl mb-3">{item.icon}</div>
              <div className="text-white font-bold mb-2">{item.label}</div>
              <div className="text-slate-400 text-sm">{item.desc}</div>
            </div>
          ))}
        </div>

        <div className="mt-8 pt-6 border-t border-blue-500/20">
          <p className="text-blue-200 text-lg font-medium italic">
            "Observability collects the evidence. AI Incident Investigator connects the evidence."
          </p>
        </div>
      </div>
    </div>
  );
}
