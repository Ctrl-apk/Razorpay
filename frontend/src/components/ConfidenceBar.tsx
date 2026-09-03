interface Props {
  score: number; // 0.0 – 1.0
}

export default function ConfidenceBar({ score }: Props) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 80 ? "bg-green-500" : pct >= 60 ? "bg-yellow-500" : "bg-red-500";

  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-[#1e2a45] rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`text-sm font-bold ${color.replace("bg-", "text-")}`}>
        {pct}%
      </span>
    </div>
  );
}
