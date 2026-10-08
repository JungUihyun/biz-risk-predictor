import { Suspense } from "react";
import DiagnosisView from "@/components/DiagnosisView";

export default function DiagnosisPage() {
  return (
    <Suspense fallback={<p className="py-20 text-center opacity-70">불러오는 중…</p>}>
      <DiagnosisView />
    </Suspense>
  );
}
