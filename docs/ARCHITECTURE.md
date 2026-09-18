# 왜 "완전 자동화"가 스크립트 하나가 아니라 예약된 Claude 세션인가

영상에서 소개된 자동화 도구는 결국 "매일 아침 완성된 쇼츠가 메일로 배송되는" 형태였습니다.
그 안을 뜯어보면 실제로는:

- 주제 선정 (LLM)
- 대본 작성 (LLM)
- TTS 생성
- 오디오 타임코드 전사
- 스토리보드/씬 프롬프트 생성 (LLM)
- 이미지 생성
- 이미지→영상 생성
- 자막 합성
- 업로드

전부 "API 호출을 순서대로, 실패하면 재시도하며" 엮은 파이프라인입니다. 우리 환경에서는
이 전체 파이프라인이 이미 **Higgsfield의 `faceless-video` 워크플로우** 하나로 통합되어
있는데, 이게 결정적으로 다른 점이 하나 있습니다:

> 이 워크플로우는 순수 REST API가 아니라, Claude 에이전트가 매 단계(Phase 0~9)마다
> 샌드박스(`sandbox_exec`)에서 명령을 실행하고, 결과를 검증하고, 필요하면 재시도하는
> "에이전트가 직접 운전하는" 파이프라인입니다. 즉 이건 `curl`을 순서대로 실행하는
> 배치 스크립트가 아니라, 판단(스타일 일관성 체크, NSFW 재시도, 자막 타이밍 검증 등)이
> 각 단계마다 필요합니다.

그래서 "완전 자동화"를 만드는 방법은 두 가지뿐입니다.

1. **이 워크플로우 전체를 처음부터 순수 코드로 다시 구현한다** — 영상 속 대표님이
   "자동화는 코딩이 필요하다"고 한 게 이 얘기입니다. 가능은 하지만 Higgsfield가
   이미 잘 만들어 둔 검증/재시도 로직을 전부 새로 짜야 해서 비효율적입니다.
2. **스케줄러가 Claude 에이전트 세션 자체를 깨워서 이 워크플로우를 실행시킨다** —
   이 저장소가 선택한 방법. Claude Code Remote의 Routine(cron)이 매일 정해진 시각에
   새 세션을 깨우고, 그 세션에게 `AGENT_PLAYBOOK.md`를 그대로 지시문으로 줍니다.
   세션은 Higgsfield MCP 도구를 호출해 영상을 완성하고, 완성된 mp4를 로컬로 받아서
   `youtube/upload.py`로 업로드까지 마칩니다.

두 번째 방법의 장점: Higgsfield가 이미 만들어 둔 견고한 파이프라인(재시도, QC 체크리스트,
스타일 일관성)을 그대로 재사용합니다. 단점: 매 실행이 "에이전트 세션 1회 실행"이라
전통적인 크론잡보다 무겁고, 세션이 꼬이면(레이트리밋, 크레딧 소진 등) 그날 업로드가
스킵될 수 있습니다. 이건 `state/uploads_log.md`를 보고 감지 가능합니다.

## 데이터 흐름

```
[Routine: 매일 08:00 KST]
        │
        ▼
Claude 세션 기동, AGENT_PLAYBOOK.md 지시대로 실행
        │
        ├─ config/channel.yaml 읽기 (니치/언어/스타일/업로드 시간)
        ├─ state/topics_used.json 읽어서 중복 주제 회피
        ├─ Higgsfield get_workflow_instructions(workflow="faceless-video") 로드
        ├─ Phase 0~9 실행 → 완성된 영상의 hosted URL + 썸네일 URL 획득
        ├─ 로컬로 다운로드 (work/output/final.mp4, thumb.jpg)
        ├─ youtube/upload.py 실행
        │     → YouTube Data API v3 videos.insert (resumable upload)
        │     → thumbnails.set
        │     → privacyStatus=private + publishAt=예약시각
        ├─ state/topics_used.json, state/uploads_log.md 갱신 후 git commit & push
        └─ 완료 보고
```

## 콘텐츠 정책 관련 메모

유튜브는 "AI 사용 여부" 자체를 문제 삼지 않습니다(공식 정책). 문제가 되는 건
"반복 가능한 동일 포맷의 대량 재탕(mass-produced/repetitive content)"입니다.
`AGENT_PLAYBOOK.md`에 주제 다양성(같은 하위 포맷 연속 금지)과 출처 검증(사실관계 확인,
특히 역사/과학 정보) 규칙을 넣어둔 것도 이 때문입니다. 업로드 시 YouTube의
"변형된 콘텐츠(altered/synthetic content)" 공개 플래그(`containsSyntheticMedia` 등,
API 지원 시)도 켜는 걸 권장합니다 — 이 저장소의 `upload.py`에는 아직 이 필드가
빠져 있으니 YouTube API 문서에서 최신 필드명을 확인 후 추가하세요.
