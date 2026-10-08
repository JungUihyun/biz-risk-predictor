// ML_API_URL이 설정되지 않았을 때(모델 학습 전 프론트엔드 개발용) 사용하는 가짜 데이터.
import type { Diagnosis, MapScore, Options, RiskLevel } from "./types";

export const mockOptions: Options = {
  quarter: "20244",
  gu: [
    { code: "11440", name: "마포구", dongs: [{ code: "11440660", name: "서교동" }, { code: "11440680", name: "합정동" }] },
    { code: "11680", name: "강남구", dongs: [{ code: "11680640", name: "역삼1동" }, { code: "11680521", name: "논현1동" }] },
    { code: "11710", name: "송파구", dongs: [{ code: "11710720", name: "잠실7동" }] },
  ],
  industries: [
    { code: "CS100001", name: "한식음식점", group: "CS1" },
    { code: "CS100010", name: "커피-음료", group: "CS1" },
    { code: "CS200001", name: "일반교습학원", group: "CS2" },
    { code: "CS300011", name: "일반의류", group: "CS3" },
  ],
};

// 코드 문자열로부터 0~1 사이의 고정된 값을 만든다 (같은 입력이면 같은 결과)
function seeded(key: string): number {
  let h = 0;
  for (const ch of key) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return (h % 1000) / 1000;
}

function level(p: number): RiskLevel {
  return p < 0.35 ? "안정" : p < 0.6 ? "보통" : "위험";
}

export function mockMap(industryCode: string): MapScore[] {
  return mockOptions.gu.flatMap((g) =>
    g.dongs.map((d) => {
      const p = seeded(d.code + industryCode);
      return { dong_code: d.code, dong_name: d.name, probability: p, level: level(p) };
    }),
  );
}

export function mockDiagnosis(dongCode: string, industryCode: string): Diagnosis | null {
  const gu = mockOptions.gu.find((g) => g.dongs.some((d) => d.code === dongCode));
  const dong = gu?.dongs.find((d) => d.code === dongCode);
  const industry = mockOptions.industries.find((i) => i.code === industryCode);
  if (!gu || !dong || !industry) return null;

  const s = seeded(dongCode + industryCode);
  const base = 0.3;
  const raw = [
    { feature: "similar_store_count", label: "유사업종 점포 수", value: 42, shap: 0.18 * s },
    { feature: "sales_qoq", label: "매출 증감률(전분기 대비)", value: -0.08, shap: 0.12 * s },
    { feature: "pop_per_store", label: "점포당 유동인구", value: 3100, shap: 0.06 - 0.1 * s },
    { feature: "close_rate", label: "현재 분기 폐업률", value: 4, shap: 0.05 },
    { feature: "floating_pop", label: "유동인구", value: 1_250_000, shap: -0.07 },
    { feature: "franchise_ratio", label: "프랜차이즈 비율", value: 0.12, shap: -0.02 },
    { feature: "sales_per_store", label: "점포당 매출액", value: 52_000_000, shap: 0.03 * s },
  ].sort((a, b) => Math.abs(b.shap) - Math.abs(a.shap));
  const probability = base + raw.reduce((acc, c) => acc + c.shap, 0);

  return {
    quarter: mockOptions.quarter,
    dong_code: dongCode,
    dong_name: dong.name,
    gu_name: gu.name,
    industry_code: industryCode,
    industry_name: industry.name,
    probability,
    level: level(probability),
    base_value: base,
    contributions: raw,
    advice: [
      {
        feature: "similar_store_count", label: "유사업종 점포 수", shap: raw[0].shap,
        finding: "동일·유사 업종 점포가 많아 경쟁이 치열합니다.",
        action: "메뉴/상품 차별화, 배달·온라인 채널 확대를 검토하세요.",
      },
      {
        feature: "sales_qoq", label: "매출 증감률(전분기 대비)", shap: raw[1].shap,
        finding: "전분기 대비 상권 매출 흐름이 좋지 않습니다.",
        action: "고정비 점검과 객단가를 높이는 상품 구성을 검토하세요.",
      },
    ],
  };
}
