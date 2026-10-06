# Vercel 자동 배포 연결

2026-10-02 사용자 요청에 따라 기존 프로젝트와 기존 주소를 유지하여 연결했다.

- 운영 주소: https://naju-little-walk.vercel.app/
- 기존 프로젝트: `reinhardt7177-labs-projects/naju-little-walk`
- 연결 저장소: `reinhardt7177-lab/naju-little-walk`
- 운영 브랜치: `codex/bitgaram-place-walks`
- Vercel Git 화면에서 ‘Connected just now’를 확인했다.
- Production → Branch Tracking을 저장하고 성공 알림과 변경된 브랜치 표시를 확인했다. 운영 도메인 자동 연결은 기존 활성 상태를 유지했다.
- GitHub 기본 main은 변경하지 않았다. 코드 변경을 위 운영 브랜치에 push하면 Vercel 자동 배포가 시작된다.
- 프레임워크는 Other, 루트는 저장소 최상위, Node.js는 24.x다. 저장소 `vercel.json`의 `npm ci`, `npm run build`, `dist/client` 설정을 사용한다.

이 문서 커밋을 push하여 첫 자동 배포를 검증한다. 실제 빌드와 운영 반영 성공 여부는 Vercel 배포 화면 및 GitHub 커밋 상태로 별도 확인한다. 문서 작성 시점에는 새 자동 배포의 성공을 미리 보증하지 않는다.

## 최초 자동 배포와 설치 오류 보완

문서 커밋 `1a274fb`를 push하자 GitHub에 Vercel pending 상태와 운영 배포가 생성됐다. 최초 배포 `8GsxaqxVADvsK6uD8qnzuJUbJk4F`는 `npm ci`에서 실패했다. 로그에 `@emnapi/core@1.11.3`, `@emnapi/runtime@1.11.3`의 잠금 파일 누락이 표시됐다.

별도 작업 폴더에서 npm으로 선택 의존성의 bundled 항목을 보완하고, 로그에 명시된 두 peer 패키지의 공식 npm 버전·다운로드 URL·integrity·의존성 정보를 조회해 잠금 파일에 추가했다. 기존 잠금 항목의 버전과 package.json은 변경하지 않았다. Linux x64/glibc 조건의 빈 작업 폴더에서 `npm ci --dry-run --ignore-scripts` 검증이 통과했다. 이 보완을 운영 브랜치에 push하여 실제 서버 설치·빌드·게시를 다시 검증한다.

## 캐릭터 배치 상태

후속 사용자 요청으로 대표 지역의 산책 시작 위치 7곳에 앱 배치를 연결했다. 아래 내용은 자동 배포 최초 연결 시점의 기록이며, 최신 구현·검증은 [시작 위치 배치 기록](naju-npc-start-placement-2026-10-02.md)을 따른다.

네 캐릭터는 `assets/npc/meshy-first-pass-20261002/`에 원본과 채색 초안으로 저장되어 있다. 지도에 NPC 로더·좌표·안내 기능을 연결하지 않았으므로 화면에는 아직 나타나지 않는다. 지역별 배치 계획은 다음과 같으며 실제 배치가 아니다.

| 캐릭터 | 예정 장소 |
|---|---|
| 배돌이 | 빛가람·한전·KENTECH 등 현대 건축 지역 |
| 버들낭자 | 금성관 등 전통 건축·복암리 고분 |
| 홍돌이 | 영산포 |
| 일반 선생님 | 다시초등학교 |

배포 준비를 위해 캐릭터 초안을 앱에 임의로 추가하지 않았다. 조형 보정과 리깅 등 미완료 작업은 NPC 제작 기록에 명시되어 있다.

공식 연결 설명: https://vercel.com/docs/git/vercel-for-github
