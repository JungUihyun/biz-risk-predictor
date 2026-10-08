"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import AdviceReport from "@/components/AdviceReport";
import RiskGauge from "@/components/RiskGauge";
import ShapWaterfall from "@/components/ShapWaterfall";
import type { Diagnosis } from "@/lib/types";

type State = { status: "loading" } | { status: "error"; message: string } | { status: "done"; data: Diagnosis };

const formatQuarter = (q: string) => `${q.slice(0, 4)}년 ${q.slice(4)}분기`;

export default function DiagnosisView() {
  const params = useSearchParams();
  const dong = params.get("dong");
  const industry = params.get("industry");
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    if (!dong || !industry) return;
    let cancelled = false;
    fetch(`/api/diagnose?dong=${dong}&industry=${industry}`)
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.detail ?? "진단에 실패했습니다.");
        if (!cancelled) setState({ status: "done", data: body });
      })
      .catch((e: Error) => !cancelled && setState({ status: "error", message: e.message }));
    return () => {
      cancelled = true;
    };
  }, [dong, industry]);

  if (!dong || !industry) return <Message text="지역과 업종을 먼저 선택해 주세요." />;
  if (state.status === "loading") return <Message text="상권 데이터를 분석하는 중입니다…" />;
  if (state.status === "error") return <Message text={state.message} />;

  const d = state.data;
  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm opacity-70">{formatQuarter(d.quarter)} 데이터 기준 · 다음 분기 폐업 위험 예측</p>
        <h1 className="mt-1 text-2xl font-bold">
          {d.gu_name} {d.dong_name} · {d.industry_name}
        </h1>
      </header>

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <Card title="폐업 위험도">
          <RiskGauge probability={d.probability} level={d.level} />
        </Card>
        <Card title="위험도에 영향을 준 요인 (SHAP)">
          <ShapWaterfall baseValue={d.base_value} probability={d.probability} contributions={d.contributions} />
        </Card>
      </div>

      <Card title="맞춤형 진단 리포트">
        <AdviceReport advice={d.advice} />
      </Card>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-black/10 p-5 dark:border-white/15">
      <h2 className="mb-4 font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function Message({ text }: { text: string }) {
  return (
    <div className="py-20 text-center">
      <p className="opacity-80">{text}</p>
      <Link href="/" className="mt-4 inline-block underline">
        처음으로
      </Link>
    </div>
  );
}
