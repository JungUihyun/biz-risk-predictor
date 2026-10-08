import type { Advice } from "@/lib/types";

export default function AdviceReport({ advice }: { advice: Advice[] }) {
  if (advice.length === 0) {
    return <p className="opacity-80">위험도를 크게 높이는 요인이 발견되지 않았습니다. 현재 상권 여건은 비교적 양호합니다.</p>;
  }
  return (
    <ol className="space-y-4">
      {advice.map((a, i) => (
        <li key={a.feature} className="rounded-xl border border-black/10 p-4 dark:border-white/15">
          <p className="text-sm font-medium text-red-600">
            요인 {i + 1} · {a.label} (+{a.shap.toFixed(3)})
          </p>
          <p className="mt-1 font-semibold">{a.finding}</p>
          <p className="mt-1 opacity-80">→ {a.action}</p>
        </li>
      ))}
    </ol>
  );
}
