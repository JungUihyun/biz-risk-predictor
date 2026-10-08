import type { NextRequest } from "next/server";
import { mockDiagnosis } from "@/lib/mock";
import { mlFetch, MOCK_MODE } from "@/lib/ml-api";

export async function GET(request: NextRequest) {
  const dong = request.nextUrl.searchParams.get("dong");
  const industry = request.nextUrl.searchParams.get("industry");
  if (!dong || !industry) {
    return Response.json({ detail: "dong, industry 파라미터가 필요합니다." }, { status: 400 });
  }

  if (MOCK_MODE) {
    const result = mockDiagnosis(dong, industry);
    return result
      ? Response.json(result)
      : Response.json({ detail: "해당 지역·업종 조합의 데이터가 없습니다." }, { status: 404 });
  }
  return mlFetch("/diagnose", { dong_code: dong, industry_code: industry });
}
