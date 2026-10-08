"use client";

import { Bar, BarChart, Cell, LabelList, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Contribution } from "@/lib/types";

const UP = "#dc2626"; // 위험도를 높인 요인
const DOWN = "#2563eb"; // 위험도를 낮춘 요인
const TOP_K = 8;

interface Step {
  label: string;
  shap: number;
  range: [number, number];
}

// 기준값(base value)에서 시작해 기여도를 하나씩 누적한 구간을 만든다.
function buildSteps(base: number, contributions: Contribution[]): Step[] {
  const top = contributions.slice(0, TOP_K);
  const rest = contributions.slice(TOP_K);
  const items = rest.length
    ? [...top, { label: `기타 ${rest.length}개 요인`, shap: rest.reduce((s, c) => s + c.shap, 0) }]
    : top;

  let cum = base;
  return items.map(({ label, shap }) => {
    const start = cum;
    cum += shap;
    return { label, shap, range: [Math.min(start, cum), Math.max(start, cum)] };
  });
}

const fmt = (v: number) => `${v > 0 ? "+" : ""}${v.toFixed(3)}`;

export default function ShapWaterfall({
  baseValue,
  probability,
  contributions,
}: {
  baseValue: number;
  probability: number;
  contributions: Contribution[];
}) {
  const steps = buildSteps(baseValue, contributions);
  const values = steps.flatMap((s) => s.range);
  // 축 눈금이 0.1 단위로 떨어지도록 범위를 반올림
  const lo = Math.max(0, Math.floor((Math.min(...values, baseValue) - 0.02) * 10) / 10);
  const hi = Math.min(1, Math.ceil((Math.max(...values, probability) + 0.02) * 10) / 10);
  const step = hi - lo > 0.4 ? 0.1 : 0.05;
  const ticks = Array.from({ length: Math.round((hi - lo) / step) + 1 }, (_, i) => +(lo + i * step).toFixed(2));

  return (
    <div>
      <ResponsiveContainer width="100%" height={56 + steps.length * 40}>
        <BarChart data={steps} layout="vertical" margin={{ top: 24, right: 56, left: 8, bottom: 8 }}>
          <XAxis type="number" domain={[lo, hi]} ticks={ticks} tickFormatter={(v: number) => v.toFixed(2)} fontSize={12} />
          <YAxis type="category" dataKey="label" width={170} fontSize={13} />
          <Tooltip
            cursor={{ fillOpacity: 0.06 }}
            formatter={(_value, _name, item) => [fmt((item.payload as Step).shap), "SHAP 기여도"]}
          />
          <ReferenceLine x={baseValue} stroke="#9ca3af" strokeDasharray="4 4"
            label={{ value: `기준값 ${baseValue.toFixed(2)}`, position: "top", fontSize: 12 }} />
          <ReferenceLine x={probability} stroke="currentColor"
            label={{ value: `예측 ${probability.toFixed(2)}`, position: "top", fontSize: 12 }} />
          <Bar dataKey="range" isAnimationActive={false}>
            {steps.map((s) => (
              <Cell key={s.label} fill={s.shap >= 0 ? UP : DOWN} />
            ))}
            <LabelList dataKey="shap" position="right" fontSize={12} formatter={(v) => fmt(Number(v))} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="mt-2 text-sm opacity-70">
        <span style={{ color: UP }}>■</span> 위험도를 높인 요인 &nbsp;
        <span style={{ color: DOWN }}>■</span> 위험도를 낮춘 요인 &nbsp;·&nbsp; 예측값 = 기준값 + SHAP 기여도의 합
      </p>
    </div>
  );
}
