import Dashboard from "@/components/Dashboard";

export default function Home() {
  return (
    <>
      <header className="mb-8">
        <h1 className="text-3xl font-bold">우리 동네 상권, 얼마나 안전할까?</h1>
        <p className="mt-2 opacity-80">
          지역과 업종을 선택하면 다음 분기 폐업 위험도를 예측하고, 그 원인을 SHAP으로 설명해 드립니다.
        </p>
      </header>
      <Dashboard />
    </>
  );
}
