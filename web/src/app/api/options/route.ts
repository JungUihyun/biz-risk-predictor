import { connection } from "next/server";
import { mockOptions } from "@/lib/mock";
import { mlFetch, MOCK_MODE } from "@/lib/ml-api";

export async function GET() {
  await connection(); // 빌드 시점에 정적으로 굳지 않도록 요청 시점에 실행
  if (MOCK_MODE) return Response.json(mockOptions);
  return mlFetch("/options");
}
