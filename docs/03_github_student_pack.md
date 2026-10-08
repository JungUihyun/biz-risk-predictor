# GitHub Student Developer Pack 활용 가이드

> 이 프로젝트를 **운영비 $0**으로 배포하기 위해 Student Pack에서 쓸 혜택과 신청 및 연결 방법을 정리했습니다.
> 조회 일자: 2026-10-08. 혜택 구성은 수시로 바뀌니 신청 전에 [education.github.com/pack](https://education.github.com/pack)에서 다시 확인하세요.

---

## 1. Student Pack 신청

### 자격
- 학위 과정에 재학 중인 학생 (대학교 포함), 13세 이상
- 활성화된 GitHub 개인 계정
- 재학 증빙: 학생증, 수강 시간표, 성적표, 재학증명서 중 하나

### 신청 절차
1. GitHub → **Settings → Emails**에서 **학교 이메일(@konkuk.ac.kr)을 추가하고 인증**합니다.
   학교 메일이 인증되어 있으면 심사가 훨씬 빨라집니다.
2. GitHub → **Settings → Billing and licensing → Education benefits**로 이동합니다.
   또는 [education.github.com](https://education.github.com)에서 **Start an application**을 누릅니다.
3. 역할로 **Student**를 고르고, 학교(Konkuk University)를 선택합니다.
4. 재학 증빙 서류를 촬영하거나 업로드합니다.
   - 영문 재학증명서(학교 포털에서 발급)가 가장 확실합니다.
   - 문서에 **이름, 학교명, 현재 학기 날짜**가 보여야 합니다.
   - GitHub 프로필의 이름(실명)과 증빙 서류의 이름이 일치하는 것이 좋습니다.
5. 제출하면 보통 며칠 안에 결과 메일이 옵니다. 거절되면 사유를 확인하고 증빙을 보완해 다시 신청합니다.

---

## 2. 이 프로젝트에서 쓸 혜택

| 용도 | 혜택 | 내용 | 비고 |
| --- | --- | --- | --- |
| **ML API 서버** | **Heroku** | 월 **$13** 크레딧 × **24개월** | 신용·체크카드 등록 필요, 18세 이상 |
| ML API 서버 (대안) | **Microsoft Azure for Students** | **$100** 크레딧(12개월) + 무료 서비스 | **카드 불필요**, 학교 메일로 가입 |
| **도메인** | **Namecheap** | `.me` 도메인 1년 무료 + SSL 1년 | |
| 개발 생산성 | GitHub Copilot Student, GitHub Pro | 코드 자동완성 등 | 재학 인증 기간 동안 |

> 프론트엔드를 올릴 **Vercel Hobby** 플랜은 Student Pack과 상관없이 누구나 무료입니다.
> v1 기획서에 있던 Render 무료 플랜은 15분 동안 요청이 없으면 잠들어서 첫 요청이 느립니다. 그래서 Student Pack 크레딧으로 **항상 켜져 있는 서버**를 쓰는 쪽으로 바꿨습니다.

---

## 3. ML API 배포 옵션 비교

| | Heroku Basic dyno | Azure App Service (F1 무료) | Render Free (참고) |
| --- | --- | --- | --- |
| 비용 | $7/월 → $13 크레딧 안에서 무료 | 무료 (크레딧 $100은 상위 플랜에 사용 가능) | 무료 |
| 슬립 | **없음 (항상 켜짐)** | 유휴 시 언로드될 수 있음, 하루 CPU 60분 제한 | 15분 유휴 시 슬립 |
| 메모리 | 512MB | 1GB | 512MB |
| 카드 | 필요 | **불필요** | 불필요 |
| 추천 | ✅ 카드가 있으면 1순위 | 카드가 없으면 | 임시 시연용 |

> Heroku **Eco** dyno($5)는 30분 동안 요청이 없으면 잠듭니다. 반드시 **Basic** dyno를 선택하세요.

### 3.1 Heroku 배포 순서 (14주차 예정)
1. [heroku.com/github-students](https://www.heroku.com/github-students/)에서 Student 혜택을 신청합니다. (Heroku 가입 → 카드 등록 → 프로그램 신청)
   - 크레딧은 **승인된 달의 1일부터** 계산되고 남은 금액은 이월되지 않습니다. 월초에 신청하는 것이 유리합니다.
2. Heroku 앱을 만들고 dyno 타입을 **Basic**으로 설정합니다.
3. 이 저장소는 모노레포라서 `api/` 폴더만 배포합니다.
   - 방법 A: `git subtree push --prefix api heroku main`
   - 방법 B: 서브디렉터리 빌드팩 사용
4. `api/Procfile`(이미 포함됨): `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. 환경변수: `ALLOWED_ORIGINS=https://<도메인>` (그리고 필요하면 `ARTIFACT_DIR`)
6. **모델 파일 처리**: `ml/artifacts/`는 git에서 제외되어 있습니다. 배포 시에는 둘 중 하나를 선택합니다.
   - 학습된 `model.joblib`, `meta.json`, `latest.parquet`을 `api/artifacts/`에 복사해 배포 브랜치에만 커밋
   - GitHub Releases에 올리고 빌드할 때 내려받기

### 3.2 Azure for Students (카드 없이)
1. [azure.microsoft.com/free/students](https://azure.microsoft.com/en-us/free/students)에서 **학교 메일**로 가입합니다.
2. **App Service**에서 Python 3.12 Linux 웹앱을 만들고 요금제를 **F1(무료)** 로 선택합니다.
3. 시작 명령: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
4. GitHub Actions 배포 연동은 Azure 포털의 **배포 센터**에서 설정합니다.

---

## 4. 도메인 연결 (Namecheap `.me` → Vercel)

1. Student Pack 페이지의 **Namecheap** 혜택에서 GitHub로 인증하고 `.me` 도메인을 등록합니다. (예: `bizrisk.me`)
2. Vercel 프로젝트 → **Settings → Domains**에 도메인을 추가합니다.
3. Vercel이 보여주는 DNS 값을 Namecheap → **Domain List → Manage → Advanced DNS**에 입력합니다.
   - 루트 도메인: `A` 레코드
   - `www`: `CNAME` 레코드
   - **값은 반드시 Vercel 화면에 표시된 것을 그대로 사용하세요.**
4. 전파되면(수 분~수 시간) Vercel이 SSL 인증서를 자동으로 발급합니다.
5. (선택) API에 서브도메인을 붙이려면 `api.<도메인>` CNAME → Heroku 앱 DNS target 값을 등록합니다.

> 무료 도메인은 **1년** 뒤 유료로 갱신됩니다. 갱신하지 않을 계획이면 자동 갱신을 꺼 두세요.

---

## 5. 체크리스트

- [ ] 학교 메일 GitHub 인증
- [ ] Student Pack 승인
- [ ] Heroku 혜택 신청 (또는 Azure for Students 가입)
- [ ] Namecheap `.me` 도메인 등록
- [ ] Vercel에 GitHub 저장소 연결 (Root Directory: `web`, 환경변수 `ML_API_URL`)
- [ ] ML API 배포 및 `ALLOWED_ORIGINS` 설정
- [ ] 도메인 연결 및 SSL 확인
- [ ] (선택) 서울 열린데이터광장 **활용사례 갤러리**에 서비스 등록
