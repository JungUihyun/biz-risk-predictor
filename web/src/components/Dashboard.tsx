"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import RiskRanking from "@/components/RiskRanking";
import { INDUSTRY_GROUPS, type Options } from "@/lib/types";

type Group = keyof typeof INDUSTRY_GROUPS;

const selectClass =
  "w-full rounded-lg border border-black/15 bg-transparent px-3 py-2 dark:border-white/20 [&>option]:text-black";

export default function Dashboard() {
  const router = useRouter();
  const [options, setOptions] = useState<Options | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [gu, setGu] = useState("");
  const [dong, setDong] = useState("");
  const [group, setGroup] = useState<Group>("CS1");
  const [industry, setIndustry] = useState("");

  useEffect(() => {
    fetch("/api/options")
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error("옵션을 불러오지 못했습니다."))))
      .then(setOptions)
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <p className="text-red-600">{error}</p>;
  if (!options) return <p className="opacity-70">지역·업종 목록을 불러오는 중…</p>;

  const dongs = options.gu.find((g) => g.code === gu)?.dongs ?? [];
  const industries = options.industries.filter((i) => i.group === group);

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-black/10 p-5 dark:border-white/15">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="space-y-1">
            <span className="text-sm font-medium">자치구</span>
            <select className={selectClass} value={gu} onChange={(e) => { setGu(e.target.value); setDong(""); }}>
              <option value="">선택하세요</option>
              {options.gu.filter((g) => g.dongs.length > 0).map((g) => (
                <option key={g.code} value={g.code}>{g.name}</option>
              ))}
            </select>
          </label>
          <label className="space-y-1">
            <span className="text-sm font-medium">행정동</span>
            <select className={selectClass} value={dong} onChange={(e) => setDong(e.target.value)} disabled={!gu}>
              <option value="">선택하세요</option>
              {dongs.map((d) => (
                <option key={d.code} value={d.code}>{d.name}</option>
              ))}
            </select>
          </label>
        </div>

        <div className="mt-6 flex gap-2" role="tablist">
          {(Object.keys(INDUSTRY_GROUPS) as Group[]).map((g) => (
            <button
              key={g}
              role="tab"
              aria-selected={group === g}
              onClick={() => { setGroup(g); setIndustry(""); }}
              className={`rounded-full px-4 py-1.5 text-sm ${
                group === g ? "bg-foreground text-background" : "border border-black/15 dark:border-white/20"
              }`}
            >
              {INDUSTRY_GROUPS[g]}
            </button>
          ))}
        </div>
        <label className="mt-4 block space-y-1">
          <span className="text-sm font-medium">세부 업종</span>
          <select className={selectClass} value={industry} onChange={(e) => setIndustry(e.target.value)}>
            <option value="">선택하세요</option>
            {industries.map((i) => (
              <option key={i.code} value={i.code}>{i.name}</option>
            ))}
          </select>
        </label>

        <button
          disabled={!dong || !industry}
          onClick={() => router.push(`/diagnosis?dong=${dong}&industry=${industry}`)}
          className="mt-6 w-full rounded-lg bg-foreground py-3 font-semibold text-background disabled:opacity-30"
        >
          폐업 위험도 진단하기
        </button>
      </section>

      {industry && <RiskRanking industry={industry} />}
    </div>
  );
}
