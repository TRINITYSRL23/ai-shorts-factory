# ai-shorts-factory

Claude + Higgsfield `faceless-video` 워크플로우로 내레이션 쇼츠를 만들고,
YouTube Data API로 자동 업로드/예약까지 하는 파이프라인.

## 구조

```
AGENT_PLAYBOOK.md      # 매 실행마다 에이전트(Claude 세션)가 따라야 하는 절차
docs/ARCHITECTURE.md   # 전체 구조와 "완전 자동화"가 실제로 어떻게 동작하는지 설명
docs/OAUTH_SETUP.md    # YouTube 업로드용 Google OAuth 자격증명 발급 방법 (본인이 직접 해야 함)
config/channel.example.yaml  # 채널 설정 예시 (니치, 언어, 업로드 시간, 톤)
youtube/upload.py      # 완성된 영상 파일을 YouTube에 업로드/예약하는 CLI 스크립트
youtube/oauth_get_token.py   # 최초 1회 OAuth 동의 후 token.json 발급용 스크립트
youtube/requirements.txt
state/topics_used.json # 이미 다룬 주제 기록 (중복 방지)
state/uploads_log.md   # 업로드 이력
```

## 이 프로젝트가 실제로 하는 일

1. **콘텐츠 생성** — Higgsfield MCP의 `faceless-video` 워크플로우(5가지 채널 타입: Explainer,
   History, Kids, Picture Story, Fairy Tale & Myth)를 Claude 세션이 직접 구동해서
   주제 선정 → 대본 → 내레이션(TTS) → 씬별 영상 생성 → 자막 합성 → 완성본(mp4)+썸네일까지
   전부 만듭니다. 이 부분은 **이미 동작하는 상태**이고, 별도 API 키가 필요 없습니다
   (이 세션에 Higgsfield가 이미 연결되어 있음).
2. **업로드/예약** — `youtube/upload.py`가 완성된 mp4를 YouTube Data API v3로 업로드하고,
   제목/설명/태그/썸네일을 세팅하고, 원하는 시각에 공개되도록 예약(`publishAt`)합니다.
3. **스케줄링** — 매일 정해진 시각에 위 1→2 과정을 실행하는 것은 Claude Code Remote의
   Routine(cron)이 담당합니다. 이 Routine이 새 세션을 깨워서 `AGENT_PLAYBOOK.md`를
   그대로 실행시키는 구조입니다. 자세한 이유는 `docs/ARCHITECTURE.md` 참고.

## 지금 막혀 있는 것 (본인이 해야 하는 일)

- [ ] YouTube 채널 준비 (없으면 새로 생성)
- [ ] `docs/OAUTH_SETUP.md` 따라서 Google Cloud에서 OAuth 클라이언트 발급 + `token.json` 생성
- [ ] `config/channel.example.yaml`을 `config/channel.yaml`로 복사해서 니치/언어/업로드 시간 확정
- [ ] 위 두 가지가 끝나면 알려주시면 → 저(Claude)가 실제로 영상 1편을 테스트로 만들어서
      업로드까지 확인 → 이상 없으면 매일 자동 실행되는 Routine을 걸어드립니다.

## 왜 지금 바로 cron을 걸지 않았는가

- 매 영상 생성은 Higgsfield 크레딧(유료)을 소비합니다.
- YouTube에 실제로 공개 업로드되는 건 되돌리기 번거로운 행동입니다.
- OAuth 자격증명 없이는 업로드 자체가 불가능합니다.

그래서 코드/문서는 전부 준비해뒀고, 실채널·실크레덴셜이 갖춰지고 1회 테스트가
성공하면 그때 자동 스케줄을 켜는 순서로 진행합니다.
