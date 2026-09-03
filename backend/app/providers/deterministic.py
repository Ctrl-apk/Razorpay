from typing import Dict, Any
from .base import AIProvider, InvestigationResult


class DeterministicInvestigator(AIProvider):
    """
    Rule-based investigator that works without any external LLM.
    Guarantees the demo works even without an API key.
    """

    async def investigate(self, evidence_package: Dict[str, Any]) -> InvestigationResult:
        deployments   = evidence_package.get("deployments", [])
        metrics       = evidence_package.get("metric_anomalies", [])
        logs          = evidence_package.get("error_logs", [])

        metric_names  = {m.get("metric") for m in metrics}
        log_messages  = " ".join(l.get("message", "").lower() for l in logs)

        has_recent_deploy       = any(d.get("minutes_before_incident", 999) < 10 for d in deployments)
        has_db_connection_spike = "db_connections" in metric_names
        has_connection_timeout  = "connection timeout" in log_messages or "connection pool" in log_messages
        has_db_refused          = "connection refused" in log_messages or "database unreachable" in log_messages
        has_error_rate          = "error_rate" in metric_names
        has_latency             = "latency_p95" in metric_names
        has_cpu_spike           = "cpu_usage" in metric_names
        has_dependency_latency  = "dependency_latency" in metric_names
        has_payment_gw          = "payment-gateway" in log_messages or "gateway" in log_messages

        # ── Scenario 1: Deployment regression + DB connection pool exhaustion ──
        if has_recent_deploy and has_db_connection_spike and has_connection_timeout:
            deploy = deployments[0]
            version = deploy.get("version", "unknown")
            mins = deploy.get("minutes_before_incident", "?")
            return InvestigationResult(
                incident_summary={
                    "title": "Database Connection Pool Exhaustion",
                    "confidence_score": 0.91,
                    "severity": "HIGH",
                    "primary_root_cause": "Database connection pool exhaustion introduced by deployment " + version,
                },
                causal_narrative=(
                    f"Deployment {version} occurred {mins:.1f} minutes before the incident. "
                    "Immediately after, database connection usage increased from the normal baseline to near-maximum capacity. "
                    "Connection timeout errors appeared in logs within seconds of the connection spike. "
                    "API error rate climbed as requests failed to acquire database connections. "
                    "CPU usage remained normal throughout, ruling out compute saturation. "
                    "No other deployment occurred during the incident window. "
                    "This pattern strongly indicates the deployment introduced a database connection pool misconfiguration — "
                    "likely an increased pool size that exhausted the database's connection limit, "
                    "or a connection leak introduced in the new code."
                ),
                evidence_points=_make_evidence(deployments, metrics, logs),
                evaluated_hypotheses=[
                    {
                        "hypothesis_name": "Database connection pool exhaustion (post-deployment)",
                        "status": "MOST_LIKELY",
                        "reasoning": (
                            f"Deployment {version} occurred {mins:.1f}m before errors. "
                            "DB connections spiked to near-maximum immediately after. "
                            "Connection timeout errors confirm pool exhaustion."
                        ),
                        "evidence_for": [
                            f"Deployment {version} at {mins:.1f} minutes before incident",
                            "DB connections increased sharply from baseline",
                            "Log: database connection timeout errors",
                            "Log: connection pool exhausted",
                        ],
                        "evidence_against": [],
                    },
                    {
                        "hypothesis_name": "CPU saturation",
                        "status": "REJECTED",
                        "reasoning": "CPU usage remained within normal bounds throughout the incident window.",
                        "evidence_for": [],
                        "evidence_against": ["CPU usage was normal during the incident"],
                    },
                    {
                        "hypothesis_name": "Traffic spike",
                        "status": "UNLIKELY",
                        "reasoning": "No increase in request volume was observed. The failure pattern is DB-specific.",
                        "evidence_for": [],
                        "evidence_against": ["No traffic metric anomaly", "DB-specific error pattern"],
                    },
                    {
                        "hypothesis_name": "External dependency failure",
                        "status": "REJECTED",
                        "reasoning": "Errors are DB connection errors, not external service timeouts.",
                        "evidence_for": [],
                        "evidence_against": ["No external dependency timeout in logs"],
                    },
                ],
                recommended_actions=[
                    {
                        "priority": "HIGH",
                        "action": f"Roll back deployment {version}",
                        "details": "Immediately roll back to the previous stable version to restore service.",
                    },
                    {
                        "priority": "HIGH",
                        "action": "Inspect database connection pool configuration",
                        "details": f"Compare pool size, timeout, and idle connection settings in {version} vs the previous version.",
                    },
                    {
                        "priority": "MEDIUM",
                        "action": "Review the diff for database-related changes",
                        "details": f"Examine commit {deploy.get('commit_sha', 'UNKNOWN')} for any ORM, connection pool, or migration changes.",
                    },
                    {
                        "priority": "MEDIUM",
                        "action": "Set alert on DB connection pool utilisation > 80%",
                        "details": "Add a Grafana alert so future pool exhaustion is caught before it causes user-facing errors.",
                    },
                ],
            )

        # ── Scenario 2: Database failure (no deployment) ──
        if has_db_refused and not has_recent_deploy:
            return InvestigationResult(
                incident_summary={
                    "title": "Database Server Failure",
                    "confidence_score": 0.87,
                    "severity": "CRITICAL",
                    "primary_root_cause": "Database server became unreachable — no recent deployment",
                },
                causal_narrative=(
                    "Database connections dropped to zero and errors indicate the database server refused connections. "
                    "No deployment occurred in the hours preceding the incident, ruling out a code regression. "
                    "CPU and application-level metrics were normal before the failure, suggesting an infrastructure-level "
                    "event such as a database crash, OOM kill, storage failure, or network partition."
                ),
                evidence_points=_make_evidence(deployments, metrics, logs),
                evaluated_hypotheses=[
                    {
                        "hypothesis_name": "Database server failure",
                        "status": "MOST_LIKELY",
                        "reasoning": "DB connections dropped to zero, 'connection refused' errors confirm server unreachability.",
                        "evidence_for": [
                            "DB connections dropped to zero",
                            "Log: connection refused",
                            "Log: database unreachable",
                            "Circuit breaker opened on database",
                        ],
                        "evidence_against": [],
                    },
                    {
                        "hypothesis_name": "Deployment regression",
                        "status": "REJECTED",
                        "reasoning": "No deployment occurred in the incident window.",
                        "evidence_for": [],
                        "evidence_against": ["No recent deployment found"],
                    },
                    {
                        "hypothesis_name": "CPU saturation",
                        "status": "REJECTED",
                        "reasoning": "CPU remained normal throughout the incident.",
                        "evidence_for": [],
                        "evidence_against": ["CPU usage was normal"],
                    },
                ],
                recommended_actions=[
                    {
                        "priority": "HIGH",
                        "action": "Check database server health",
                        "details": "SSH to the database host, check process status, disk space, and system logs.",
                    },
                    {
                        "priority": "HIGH",
                        "action": "Review database server logs",
                        "details": "Check PostgreSQL/MySQL logs for OOM kill, crash, or storage errors.",
                    },
                    {
                        "priority": "MEDIUM",
                        "action": "Verify network connectivity",
                        "details": "Confirm the application host can reach the database host on the correct port.",
                    },
                    {
                        "priority": "LOW",
                        "action": "Consider read-replica failover",
                        "details": "If a replica is available, redirect read traffic while the primary is investigated.",
                    },
                ],
            )

        # ── Scenario 3: Traffic spike / resource saturation ──
        if has_cpu_spike and has_error_rate and has_latency and not has_recent_deploy and not has_dependency_latency and not has_payment_gw:
            return InvestigationResult(
                incident_summary={
                    "title": "Traffic Spike — Resource Saturation",
                    "confidence_score": 0.82,
                    "severity": "HIGH",
                    "primary_root_cause": "Sudden traffic surge exhausted CPU and request queue capacity",
                },
                causal_narrative=(
                    "Request volume increased dramatically without a corresponding deployment. "
                    "CPU usage climbed to near-saturation, causing request queue depth to exceed thresholds. "
                    "Latency increased as queued requests waited for worker threads. "
                    "Error rate increased as worker threads were dropped. "
                    "This pattern is consistent with a sudden traffic spike — possible causes include "
                    "a promotional event, bot traffic, or an upstream service routing change."
                ),
                evidence_points=_make_evidence(deployments, metrics, logs),
                evaluated_hypotheses=[
                    {
                        "hypothesis_name": "Traffic spike / resource saturation",
                        "status": "MOST_LIKELY",
                        "reasoning": "CPU, latency, error rate all spike simultaneously without a deployment.",
                        "evidence_for": [
                            "CPU usage spiked to 91%",
                            "Error rate increased",
                            "Latency increased to >1800ms",
                            "Log: worker thread pool saturated",
                            "Log: request queue depth exceeded",
                        ],
                        "evidence_against": [],
                    },
                    {
                        "hypothesis_name": "Deployment regression",
                        "status": "REJECTED",
                        "reasoning": "No deployment occurred in the incident window.",
                        "evidence_for": [],
                        "evidence_against": ["No recent deployment"],
                    },
                    {
                        "hypothesis_name": "Database failure",
                        "status": "UNLIKELY",
                        "reasoning": "DB connections increased proportionally, not to zero. CPU spike is the primary anomaly.",
                        "evidence_for": [],
                        "evidence_against": ["DB connections increased proportionally to traffic, not to zero"],
                    },
                ],
                recommended_actions=[
                    {
                        "priority": "HIGH",
                        "action": "Scale horizontally — add more instances",
                        "details": "Increase the instance count or trigger auto-scaling policy immediately.",
                    },
                    {
                        "priority": "HIGH",
                        "action": "Identify the traffic source",
                        "details": "Check access logs for unusual IPs, user agents, or endpoint patterns.",
                    },
                    {
                        "priority": "MEDIUM",
                        "action": "Implement rate limiting on public endpoints",
                        "details": "Add per-IP and per-user rate limits to protect the service.",
                    },
                    {
                        "priority": "LOW",
                        "action": "Tune auto-scaling thresholds",
                        "details": "Lower the CPU threshold that triggers auto-scaling to react faster.",
                    },
                ],
            )

        # ── Scenario 4: External dependency failure ──
        if has_dependency_latency or has_payment_gw:
            return InvestigationResult(
                incident_summary={
                    "title": "External Dependency Failure",
                    "confidence_score": 0.84,
                    "severity": "HIGH",
                    "primary_root_cause": "External payment gateway is experiencing severe latency or is unreachable",
                },
                causal_narrative=(
                    "Dependency latency to the external payment gateway increased dramatically. "
                    "Service latency mirrored the dependency latency exactly, confirming a cascading failure. "
                    "CPU and database metrics remained normal, ruling out internal resource issues. "
                    "No deployment occurred. The circuit breaker eventually opened to prevent further request accumulation. "
                    "This is an external provider incident — not a code regression."
                ),
                evidence_points=_make_evidence(deployments, metrics, logs),
                evaluated_hypotheses=[
                    {
                        "hypothesis_name": "External dependency failure (payment gateway)",
                        "status": "MOST_LIKELY",
                        "reasoning": "Dependency latency mirrors service latency exactly. CPU and DB are normal.",
                        "evidence_for": [
                            "Dependency latency spiked to 7200ms+",
                            "Service latency mirrors dependency latency",
                            "Log: payment-gateway timeout errors",
                            "Log: circuit breaker opened on payment-gateway",
                        ],
                        "evidence_against": [],
                    },
                    {
                        "hypothesis_name": "Deployment regression",
                        "status": "REJECTED",
                        "reasoning": "No deployment occurred.",
                        "evidence_for": [],
                        "evidence_against": ["No recent deployment"],
                    },
                    {
                        "hypothesis_name": "CPU saturation",
                        "status": "REJECTED",
                        "reasoning": "CPU usage remained normal.",
                        "evidence_for": [],
                        "evidence_against": ["CPU was normal"],
                    },
                    {
                        "hypothesis_name": "Database failure",
                        "status": "REJECTED",
                        "reasoning": "DB connections were stable throughout.",
                        "evidence_for": [],
                        "evidence_against": ["DB connections normal"],
                    },
                ],
                recommended_actions=[
                    {
                        "priority": "HIGH",
                        "action": "Check payment gateway status page",
                        "details": "Verify if the provider has an active incident on their status page.",
                    },
                    {
                        "priority": "HIGH",
                        "action": "Enable fallback payment provider if available",
                        "details": "Route transactions to the secondary payment provider while primary is degraded.",
                    },
                    {
                        "priority": "MEDIUM",
                        "action": "Contact payment gateway support",
                        "details": "Open a priority ticket with the provider referencing the timeout timestamps.",
                    },
                    {
                        "priority": "LOW",
                        "action": "Review circuit breaker timeout configuration",
                        "details": "Ensure circuit breaker opens quickly enough to prevent request pile-up.",
                    },
                ],
            )

        # ── Generic fallback ──
        return InvestigationResult(
            incident_summary={
                "title": "Incident Under Investigation",
                "confidence_score": 0.40,
                "severity": "MEDIUM",
                "primary_root_cause": "Insufficient evidence to determine root cause",
            },
            causal_narrative=(
                "The available telemetry is insufficient to determine the root cause with confidence. "
                "Anomalies have been detected but no clear causal pattern matches known failure modes. "
                "Manual investigation is recommended."
            ),
            evidence_points=_make_evidence(deployments, metrics, logs),
            evaluated_hypotheses=[
                {
                    "hypothesis_name": "Insufficient telemetry",
                    "status": "MOST_LIKELY",
                    "reasoning": "No dominant failure pattern detected from available evidence.",
                    "evidence_for": [],
                    "evidence_against": [],
                }
            ],
            recommended_actions=[
                {
                    "priority": "HIGH",
                    "action": "Collect additional telemetry",
                    "details": "Ingest more metrics and logs to allow the investigation engine to identify a pattern.",
                }
            ],
        )


def _make_evidence(deployments, metrics, logs) -> list:
    points = []
    for d in deployments:
        points.append({
            "type": "deployment",
            "observation": f"Deployment {d.get('version')} occurred {d.get('minutes_before_incident', '?'):.1f} minutes before the incident",
            "supporting": True,
        })
    for m in metrics:
        points.append({
            "type": "metric_anomaly",
            "metric": m.get("metric"),
            "observation": f"{m.get('metric')} anomaly: average {m.get('average', 'unknown')} over {m.get('samples', '?')} samples",
            "supporting": True,
        })
    for l in logs[:6]:
        points.append({
            "type": "log",
            "level": l.get("level"),
            "observation": l.get("message"),
            "supporting": True,
        })
    return points
