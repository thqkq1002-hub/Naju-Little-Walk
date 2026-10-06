# 배돌이 손·모자 보정 v6

2026-10-02. 기존 원본과 사용자 수정본을 보존한 별도 제작 폴더다.

- `reference-a-pose.png`: 내장 imagegen 이미지 편집 결과. 앞선 배돌이 정면 참조를 바탕으로 손을 모자에서 떨어뜨리고 빈손의 낮은 A 자세로 변경했다.
- `baedoli-meshy71-original.glb`: 새 Meshy 7.1 원본, 596,448삼각형. 직접 덮어쓰지 않는다.
- `baedoli-rigged-v6.blend`: 고해상도 텍스처를 내장한 편집용 리깅 파일.
- `baedoli-rigged-v6.glb`: 웹에 전달하는 별도 60,000삼각형·2K WebP 내장 GLB. `public/models/npc/baedoli-v6.glb`와 동일하다.
- `baedoli-greeting-preview.png`: 최종 보정 리그에서 직접 렌더한 인사 자세.
- `generation-record.json`: 생성 작업·설정·전후 잔액. 960 → 925, 실제 35크레딧.
- `rig-verification.json`: 메시·뼈·동작·웹 크기 정보.

## 새 참조의 편집 지시

기존 노란 배 얼굴, 검은 타원 눈, 크림색 볼 반점, 미소, 주황 밀짚모자의 연속된 넓은 테두리, 파란 목수건, 크림색 몸과 짧은 다리·발을 유지한다. 손의 작은 배는 제거하고 두 팔을 몸에서 떨어뜨린 낮은 A 자세로 내린다. 빈손의 둥근 손가락이 분명히 보이며 손은 턱과 모자에서 멀리 떨어져야 한다. 엄지 포즈, 얼굴·모자에 닿는 손, 찢어진 모자 테두리는 피한다. 흰 배경, 정면 전신, 발과 모자 전체가 보이는 고품질 3D 제품 렌더, 글자나 별도 소품 없음.

## 제작 순서

`scripts/meshy_baedoli_clean.py`는 API 키를 프로세스 환경에서 읽는 재개 가능한 생성 스크립트다. 이미 성공한 상태가 있으면 새 유료 요청을 만들지 않는다. `scripts/rig_meshy71_npc.py -- baedoli v6`로 처음 리깅하고 `scripts/refine_npc_skin.py -- baedoli v6`로 손·머리 영향을 분리한다. `scripts/export_npc_web.py -- baedoli v6`은 편집용 원본의 텍스처 해상도를 바꾸지 않고 웹 사본만 내보낸다.

손과 모자가 겹치던 이전 포즈 대신 새 형태를 사용한다. 다섯 동작은 몸과 팔의 포즈 애니메이션이며 개별 손가락 제스처·얼굴 표정·입술 동기화는 포함하지 않는다. 단일 정면 자료에 없는 후면은 AI 추정이다.
