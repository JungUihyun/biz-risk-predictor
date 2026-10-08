import { LEVEL_COLOR, type RiskLevel } from "@/lib/types";

const BANDS: [number, number, RiskLevel][] = [
  [0, 0.35, "안정"],
  [0.35, 0.6, "보통"],
  [0.6, 1, "위험"],
];
const CX = 120;
const CY = 120;
const R = 100;

// 확률 p(0~1)를 반원 위의 좌표로 변환 (왼쪽 끝 0, 오른쪽 끝 1)
function point(p: number, r = R) {
  const angle = Math.PI * (1 - p);
  return { x: CX + r * Math.cos(angle), y: CY - r * Math.sin(angle) };
}

function arc(from: number, to: number) {
  const a = point(from);
  const b = point(to);
  return `M ${a.x} ${a.y} A ${R} ${R} 0 0 1 ${b.x} ${b.y}`;
}

export default function RiskGauge({ probability, level }: { probability: number; level: RiskLevel }) {
  const p = Math.min(Math.max(probability, 0), 1);
  const needle = point(p, R - 18);

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 240 140" className="w-full max-w-xs" role="img" aria-label={`폐업 위험도 ${Math.round(p * 100)}%`}>
        {BANDS.map(([from, to, name]) => (
          <path key={name} d={arc(from, to)} stroke={LEVEL_COLOR[name]} strokeWidth={18} fill="none" opacity={0.85} />
        ))}
        <line x1={CX} y1={CY} x2={needle.x} y2={needle.y} stroke="currentColor" strokeWidth={4} strokeLinecap="round" />
        <circle cx={CX} cy={CY} r={7} fill="currentColor" />
      </svg>
      <p className="-mt-2 text-4xl font-bold tabular-nums">{(p * 100).toFixed(1)}%</p>
      <p className="mt-1 text-lg font-semibold" style={{ color: LEVEL_COLOR[level] }}>
        {level}
      </p>
    </div>
  );
}
