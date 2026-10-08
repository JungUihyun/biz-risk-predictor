"use client";

// TODO: 행정동 경계 GeoJSON을 확보하면 서울시 지도(색상 표시)로 교체
import Link from "next/link";
import { useEffect, useState } from "react";
import { LEVEL_COLOR, type MapScore } from "@/lib/types";

export default function RiskRanking({ industry }: { industry: string }) {
  const [scores, setScores] = useState<{ industry: string; rows: MapScore[] } | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`/api/map?industry=${industry}`)
      .then((res) => (res.ok ? res.json() : []))
      .then((rows: MapScore[]) => !cancelled && setScores({ industry, rows }));
    return () => {
      cancelled = true;
    };
  }, [industry]);

  if (!scores || scores.industry !== industry) return <p className="opacity-70">지역별 위험도를 불러오는 중…</p>;
  const top = [...scores.rows].sort((a, b) => b.probability - a.probability).slice(0, 10);

  return (
    <section className="rounded-2xl border border-black/10 p-5 dark:border-white/15">
      <h2 className="mb-4 font-semibold">이 업종의 고위험 행정동 Top 10</h2>
      <ul className="divide-y divide-black/5 dark:divide-white/10">
        {top.map((s) => (
          <li key={s.dong_code}>
            <Link
              href={`/diagnosis?dong=${s.dong_code}&industry=${industry}`}
              className="flex items-center justify-between py-2 hover:opacity-70"
            >
              <span>{s.dong_name}</span>
              <span className="flex items-center gap-2 tabular-nums">
                {(s.probability * 100).toFixed(1)}%
                <span className="rounded px-2 py-0.5 text-xs text-white" style={{ background: LEVEL_COLOR[s.level] }}>
                  {s.level}
                </span>
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
