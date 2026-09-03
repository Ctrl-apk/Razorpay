export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type IncidentStatus = "ACTIVE" | "INVESTIGATING" | "RESOLVED" | "FALSE_ALARM";
export type HypothesisStatus = "MOST_LIKELY" | "LIKELY" | "UNLIKELY" | "REJECTED";
export type Priority = "HIGH" | "MEDIUM" | "LOW";

export interface Incident {
  id: string;
  incident_id: string;
  service: string;
  start_time: string;
  end_time?: string;
  severity: Severity;
  status: IncidentStatus;
  trigger_metrics?: Record<string, unknown>;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Hypothesis {
  hypothesis_name: string;
  status: HypothesisStatus;
  reasoning: string;
  evidence_for: string[];
  evidence_against: string[];
}

export interface RecommendedAction {
  priority: Priority;
  action: string;
  details: string;
}

export interface EvidencePoint {
  type: "metric_anomaly" | "log" | "deployment";
  observation: string;
  supporting: boolean;
  metric?: string;
  level?: string;
  version?: string;
}

export interface IncidentSummary {
  title: string;
  confidence_score: number;
  severity: Severity;
  primary_root_cause: string;
}

export interface Investigation {
  id: string;
  incident_id: string;
  root_cause?: string;
  confidence_score?: number;
  causal_narrative?: string;
  evidence_package?: EvidencePackage;
  hypotheses?: Hypothesis[];
  recommended_actions?: RecommendedAction[];
  created_at: string;
  updated_at: string;
}

export interface EvidencePackage {
  incident: {
    incident_id: string;
    service: string;
    started_at: string;
  };
  deployments: DeploymentEvidence[];
  metric_anomalies: MetricEvidence[];
  error_logs: LogEvidence[];
  timeline: TimelineEvent[];
}

export interface DeploymentEvidence {
  version: string;
  timestamp: string;
  commit_sha?: string;
  author?: string;
  minutes_before_incident: number;
  strength: number;
}

export interface MetricEvidence {
  metric: string;
  average: number;
  samples: number;
  first_observation: string;
}

export interface LogEvidence {
  timestamp: string;
  level: string;
  message: string;
}

export interface TimelineEvent {
  timestamp: string;
  type: "deployment" | "metric" | "log" | "incident_start";
  version?: string;
  commit_sha?: string;
  metric_name?: string;
  value?: number;
  unit?: string;
  level?: string;
  message?: string;
}

export interface Scenario {
  name: string;
}
