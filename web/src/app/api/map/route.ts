import type { NextRequest } from "next/server";
import { mockMap } from "@/lib/mock";
import { mlFetch, MOCK_MODE } from "@/lib/ml-api";

export async function GET(request: NextRequest) {
  const industry = request.nextUrl.searchParams.get("industry");
  if (!industry) {
    return Response.json({ detail: "industry 파라미터가 필요합니다." }, { status: 400 });
  }
  if (MOCK_MODE) return Response.json(mockMap(industry));
  return mlFetch("/map", { industry_code: industry });
}
