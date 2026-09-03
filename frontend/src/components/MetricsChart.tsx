import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { TimelineEvent } from "../types";

interface Props {
  events: TimelineEvent[];
  metricName: string;
  color?: string;
  incidentStart?: string;
}

export default function MetricsChart({
  events,
  metricName,
  color = "#3b82f6",
  incidentStart,
}: Props) {
  const data = events
    .filter((e) => e.type === "metric" && e.metric_name === metricName)
    .map((e) => ({
      time: new Date(e.timestamp).toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }),
      value: e.value ?? 0,
    }));

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-24 text-slate-500 text-xs">
        No data for {metricName}
      </div>
    );
  }

  // Find incident reference line time
  const incidentTime = incidentStart
    ? new Date(incidentStart).toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      })
    : undefined;

  return (
    <ResponsiveContainer width="100%" height={100}>
      <LineChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e2a45" />
        <XAxis dataKey="time" tick={{ fill: "#64748b", fontSize: 10 }} />
        <YAxis tick={{ fill: "#64748b", fontSize: 10 }} />
        <Tooltip
          contentStyle={{ background: "#0f1629", border: "1px solid #1e2a45", borderRadius: 8 }}
          labelStyle={{ color: "#94a3b8" }}
          itemStyle={{ color }}
        />
        {incidentTime && (
          <ReferenceLine x={incidentTime} stroke="#ef4444" strokeDasharray="4 2" label="" />
        )}
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
