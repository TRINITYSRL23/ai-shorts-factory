# YouTube 업로드용 OAuth 자격증명 발급 (직접 하셔야 하는 부분)

Claude(저)는 사용자분 소유의 Google 계정에 로그인하거나 OAuth 동의를 대신 눌러드릴 수
없습니다. 아래는 본인이 직접 하셔야 하는 절차입니다. 다 끝나면 `token.json` 파일 하나가
나오는데, 그것만 저한테 안전하게 전달(또는 Claude Code Remote 환경변수/시크릿으로 등록)
해주시면 이후 업로드는 제가 대신 수행합니다.

## 1. Google Cloud 프로젝트 생성 + API 활성화

1. https://console.cloud.google.com 접속, 새 프로젝트 생성 (예: `ai-shorts-factory`)
2. 좌측 메뉴 → "API 및 서비스" → "라이브러리" → **YouTube Data API v3** 검색 후 사용 설정

## 2. OAuth 동의 화면 설정

1. "API 및 서비스" → "OAuth 동의 화면"
2. User Type: **외부(External)** 선택 (개인 Gmail 계정이면 이것만 가능)
3. 앱 이름/이메일 등 필수 항목만 채워서 저장
4. "범위(Scopes)" 단계에서 `https://www.googleapis.com/auth/youtube.upload` 추가
5. "테스트 사용자"에 본인 Gmail 주소를 추가

### ⚠️ 반드시 알아야 하는 제약: 테스트 모드는 refresh token이 7일마다 만료됩니다

OAuth 동의 화면이 "테스트(Testing)" 상태인 동안 발급되는 refresh token은 **7일 후
자동 만료**됩니다. 즉 매주 다시 로그인해서 재동의해야 하므로 "완전 자동화"가 깨집니다.

**해결책 (verification 없이 가능한 실질적 방법):**
"OAuth 동의 화면" → "앱 게시(Publish App)" 버튼을 눌러 상태를 **"프로덕션(In production)"**
으로 바꾸세요. `youtube.upload`는 Google이 "제한된 범위(restricted scope)"로 분류해서
정식으로는 보안 심사(verification)를 요구하지만, **본인 1인만 쓰는 개인용 앱**이라면
심사 없이 프로덕션으로 전환해도 실제로는 동작합니다. 다만 동의 화면에 "Google에서 확인하지
않은 앱" 경고가 뜨는데, 본인 계정으로 최초 1회 로그인할 때 "고급(Advanced)" →
"(앱 이름)(으)로 이동(안전하지 않음)"을 클릭하면 정상적으로 진행됩니다. 이 상태에서 받은
refresh token은 만료 없이(수동으로 취소하지 않는 한) 계속 씁니다.

만약 앱이 커져서 여러 사람이 쓰게 되거나 Google이 심사를 요구하면 그때 공식 verification
절차(개인정보처리방침 URL, 스코프 사용 목적 설명, 경우에 따라 보안 평가)를 진행하면 됩니다.
개인 자동화 용도로는 보통 필요 없습니다.

## 3. OAuth 클라이언트(데스크톱 앱) 생성

1. "API 및 서비스" → "사용자 인증 정보" → "+ 사용자 인증 정보 만들기" → "OAuth 클라이언트 ID"
2. 애플리케이션 유형: **데스크톱 앱**
3. 생성 후 JSON 다운로드 → 파일명을 `client_secret.json`으로 저장
   (이 파일은 **절대 git에 커밋하지 마세요** — `.gitignore`에 이미 포함되어 있습니다)

## 4. 최초 1회 로그인해서 token.json 만들기

로컬 PC나 이 세션에서:

```bash
cd youtube
pip install -r requirements.txt
python oauth_get_token.py --client-secret client_secret.json --out token.json
```

브라우저가 뜨면 본인 YouTube 채널을 소유한 Google 계정으로 로그인 → 동의.
(브라우저가 없는 원격 환경이면 `oauth_get_token.py`가 콘솔에 출력하는 URL을 로컬 브라우저에서
열고, 리디렉션된 코드를 다시 터미널에 붙여넣는 방식으로도 동작합니다 — 스크립트 안내를 따르세요.)

완료되면 `token.json`이 생성됩니다. 이 파일 하나면 이후 업로드는 전부 무인으로 동작합니다.

## 5. 저에게 전달하는 방법 (택1)

- Claude Code Remote 환경의 환경변수/시크릿으로 `token.json`의 내용을 등록
- 또는 이 저장소의 CI/시크릿 스토어에 등록 (레포에 직접 커밋 금지)

준비되면 알려주세요 — 실제 업로드 테스트를 1건 진행하겠습니다.
