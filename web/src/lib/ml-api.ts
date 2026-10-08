// 서버(Route Handler)에서만 사용: FastAPI ML 서버로 요청을 프록시한다.
import "server-only";

const ML_API_URL = process.env.ML_API_URL;

export const MOCK_MODE = !ML_API_URL;

export async function mlFetch(path: string, params?: Record<string, string>): Promise<Response> {
  const url = new URL(path, ML_API_URL);
  for (const [k, v] of Object.entries(params ?? {})) url.searchParams.set(k, v);
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(60_000) });
    return new Response(res.body, { status: res.status, headers: { "content-type": "application/json" } });
  } catch {
    return Response.json({ detail: "ML 서버에 연결할 수 없습니다." }, { status: 502 });
  }
}
