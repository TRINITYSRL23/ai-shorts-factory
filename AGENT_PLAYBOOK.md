# 에이전트 실행 플레이북 (Routine이 매일 이 지시를 실행합니다)

이 문서는 사람이 아니라, 매일 예약 실행되는 Claude 세션이 읽고 그대로 따르는
절차서입니다. 사람이 수동으로 실행할 때도 동일하게 따르면 됩니다.

## 0. 사전 조건 확인

- `config/channel.yaml`이 존재하는지 확인 (없으면 `config/channel.example.yaml`을
  복사하라고 알리고 중단)
- `youtube/token.json`(또는 `$YT_TOKEN_PATH`)이 존재하는지 확인 (없으면
  `docs/OAUTH_SETUP.md`를 안내하고 중단 — 업로드 없이 영상만 만들어서 사람 확인을
  기다리는 것도 옵션이나, 기본은 여기서 멈춤)
- Higgsfield MCP 도구(`generate_*`, `get_workflow_instructions` 등)가 이 세션에
  연결돼 있는지 확인. 연결 안 돼 있으면 중단하고 보고.

## 1. 주제 선정

1. `state/topics_used.json`을 읽어서 최근 다룬 주제 목록 확인
2. `config/channel.yaml`의 `niche_description`을 바탕으로 후보 주제 5개를 제시
   (영상 속 방식과 동일: 검증 가능한 사실 기반, 흥미로운 반전 포인트가 있는 것)
3. `diversity.avoid_repeat_within_last_n_topics` 규칙에 걸리는 주제는 제외
4. 가장 매력적인 것 1개를 최종 선택하고, 선택 이유를 한 줄로 기록

## 2. 영상 제작 — Higgsfield `faceless-video` 워크플로우 그대로 실행

1. `get_workflow_instructions({ workflow: "faceless-video" })` 로 SKILL.md 로드
2. `channel_type`에 맞는 타입(History/Explainer/…)으로 Phase 0(Intake)부터 Phase 9
   (Deliver)까지 **순서대로, 단계 건너뛰지 말고** 실행
   - `channel.yaml`의 `style_preset`, `narrator_voice`, `video.*` 설정을 Intake에 그대로 반영
   - Phase 5(Voiceover)는 `narrator` 워크플로우를, Phase 7(Caption)은 `subtitles`
     워크플로우를 SKILL.md 지시대로 로드해서 따를 것 (즉흥적으로 TTS/자막을 만들지 말 것)
   - GOLDEN RULES와 FINAL QC CHECKLIST를 반드시 통과할 것
3. Phase 9에서 반환되는 **hosted URL**(완성 영상)과 썸네일 URL을 확보
4. 로컬로 다운로드:
   ```
   curl -fL '<final_video_url>' -o work/output/final.mp4
   curl -fL '<thumbnail_url>' -o work/output/thumb.jpg
   ```

## 3. 업로드 메타데이터 작성

- 제목: 클릭을 유도하되 낚시성/허위 없이. 60자 이내 권장.
- 설명: 2~3문장 요약 + 출처/근거 한 줄 + `config.upload.default_hashtags`
- 태그: 주제 관련 키워드 5~10개
- `publish_at`: 오늘 날짜 + `config.upload.publish_time_kst`를 UTC RFC3339로 변환

## 4. 업로드 실행

```
cd youtube
python upload.py \
  --video ../work/output/final.mp4 \
  --thumbnail ../work/output/thumb.jpg \
  --title "<제목>" \
  --description "<설명>" \
  --tags "<태그1,태그2,...>" \
  --category-id <config.upload.category_id> \
  --publish-at <RFC3339> \
  --token token.json
```

성공하면 콘솔에 `https://youtu.be/<videoId>`가 출력됩니다.

## 5. 상태 기록 + 커밋

1. `state/topics_used.json`에 오늘 주제 추가
2. `state/uploads_log.md`에 한 줄 추가: 날짜, 제목, video URL, 상태(성공/실패+사유)
3. `work/` 산출물은 커밋하지 말 것 (`.gitignore`에 포함됨) — 로그/상태 파일만 커밋
4. `git add state/ && git commit -m "auto: <날짜> 업로드 - <제목>" && git push`

## 실패 시

- 어느 단계든 실패하면 **다음 단계로 넘어가지 말고** 무엇이 실패했는지
  `state/uploads_log.md`에 "실패" 상태로 기록하고 종료
- Higgsfield 크레딧 부족, YouTube 쿼터 초과, token.json 만료 등은 사람 개입이
  필요한 문제이므로 자동 재시도하지 말고 명확히 보고
