import type { Metadata } from "next";
import Link from "next/link";
import { Noto_Sans_KR } from "next/font/google";
import "./globals.css";

const notoSansKr = Noto_Sans_KR({
  variable: "--font-noto-sans-kr",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  title: "Biz Risk Predictor · 상권 폐업 위험도 진단",
  description: "서울시 상권 데이터와 머신러닝·SHAP으로 폐업 위험도와 그 원인을 진단합니다.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ko" className={`${notoSansKr.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <nav className="border-b border-black/10 dark:border-white/15">
          <div className="mx-auto flex max-w-5xl items-center px-4 py-3">
            <Link href="/" className="font-bold">Biz Risk Predictor</Link>
          </div>
        </nav>
        <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">{children}</main>
        <footer className="py-6 text-center text-xs opacity-60">
          데이터: 서울 열린데이터광장 상권분석서비스 · 데이터사이언스활용 개별 프로젝트
        </footer>
      </body>
    </html>
  );
}
