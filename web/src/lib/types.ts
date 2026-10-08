export type RiskLevel = "안정" | "보통" | "위험";

export interface Options {
  quarter: string;
  gu: { code: string; name: string; dongs: { code: string; name: string }[] }[];
  industries: { code: string; name: string; group: "CS1" | "CS2" | "CS3" }[];
}

export interface MapScore {
  dong_code: string;
  dong_name: string;
  probability: number;
  level: RiskLevel;
}

export interface Contribution {
  feature: string;
  label: string;
  value: number | null;
  shap: number;
}

export interface Advice {
  feature: string;
  label: string;
  shap: number;
  finding: string;
  action: string;
}

export interface Diagnosis {
  quarter: string;
  dong_code: string;
  dong_name: string;
  gu_name: string;
  industry_code: string;
  industry_name: string;
  probability: number;
  level: RiskLevel;
  base_value: number;
  contributions: Contribution[];
  advice: Advice[];
}

export const INDUSTRY_GROUPS = { CS1: "외식업", CS2: "서비스업", CS3: "소매업" } as const;

export const LEVEL_COLOR: Record<RiskLevel, string> = {
  안정: "#16a34a",
  보통: "#eab308",
  위험: "#dc2626",
};
