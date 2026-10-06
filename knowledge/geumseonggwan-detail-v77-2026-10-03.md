# 금성관 고도화 v77

2026-10-03. 운영 범위는 금성관 경내입니다. v76 편집본을 읽어 **새 Blender 수정본**을 만들고 GLB로 내보냈습니다.

## 사진·설명으로 확인한 부분

- [국가유산 디지털 서비스](https://digital.khs.go.kr/heri/heriDetail.do?ctptNo=1123620370000&ctptUid=13898859673312200636): 정면 5칸·측면 4칸, 팔작지붕·겹처마, 1출목 3익공, 2고주 7량, 금모로 단청 설명을 구조 기준으로 사용했습니다.
- [한국민족문화대백과사전](https://encykorea.aks.ac.kr/Article/E0011462)의 2009년 정측면 사진: 정청과 낮은 익헌의 높이 관계, 회색 기와, 갈색 기둥·녹색 단청, 흙마당과 박석길의 색 관계를 검토했습니다. 기존 자료는 `knowledge/sources/geumseonggwan-v76`에 있습니다.
- OSM 건물 윤곽은 `knowledge/sources/geumseonggwan.osm`을 그대로 사용했습니다. 지도 출처와 ODbL 안내를 유지합니다.

백과사전의 오래된 공포 분류보다 국가유산 서비스의 세부 구조 설명을 우선했습니다. 현장 실측도나 최신 보수 도면을 확보한 상태는 아닙니다.

## 이번 제작

| 부분 | 수정 내용 |
|---|---|
| 공포 | 정청·망화루의 단순 블록을 제거하고 20개 위치에 세 단의 곡선형 익공과 틈, 색 테두리 제작 |
| 단청 | 과한 채도 완화, 보 끝에 곡선 문양 추가 |
| 재질 | 직접 만든 나뭇결·옹이, 흙의 색 변화, 한지 섬유의 색·거칠기·노멀 맵 |
| 석재 | 계단·기단·주초 모서리 18mm 베벨, 박석의 색 변화 |
| 문살 | 기존 격자 유지, 닫힌 문짝에 작은 철제 고리·경첩 추가 |
| 지붕 | 팔작지붕 측면에 별도 둥근 기와 골 추가 |
| 화면 | 정청 정면·처마·공포·망화루 보기, 높은 대상을 보는 카메라 높이 보정, 전체 보기·걷기 전환 시 시야 복원 |
| 그림자 | 금성관 범위에 그림자 영역 집중, 부드러운 필터, 아주 얇은 장식·한지·박석의 불필요한 그림자 제외 |

**추정한 부분:** 익공의 세부 곡률·각 부재 치수, 개별 단청 문양, 고리·경첩의 정확한 형태·위치, 표면 노후 정도와 나무 수형은 사진을 참고한 제작 해석입니다. 특정 연도의 금성관을 정밀 실측 복원한 모델로 표기하지 않습니다. 사진을 그대로 텍스처로 복사하지 않았습니다.

## 원본 보존과 재생성

- 보존 원본: `outputs/geumseonggwan-exclusive-v76/geumseonggwan-exclusive-v76.blend`
- 새 편집본: `outputs/geumseonggwan-v77/geumseonggwan-v77.blend`
- 재질 생성: `scripts/make_geumseonggwan_materials_v77.py`
- Blender 수정·내보내기: `scripts/refine_geumseonggwan_v77.py`
- 검토 렌더: `scripts/render_geumseonggwan_v77.py`
- 재질 원본: `assets/geumseonggwan-v77/materials`의 1024px PNG. 웹 GLB에는 공유 512px WebP를 포함합니다.

생성 스크립트는 **이 v77 파일을 사용자가 직접 편집한 뒤에는 다시 실행하지 않습니다.** 후속 제작은 편집본을 읽어 별도 버전으로 저장합니다. `.blend`, 실행 파일과 검토용 출력은 배포에 넣지 않습니다.

## 품질·성능 확인

- v76 원본 SHA-256 일치. 벽·문·바닥의 충돌 배열을 깊은 비교로 확인했고 기존 값이 그대로입니다.
- 기존 계단의 상면 높이와 문 통과 폭 유지. 석재 베벨은 기존 충돌 외곽 안쪽에서 처리했습니다.
- 새 장면 542개 객체, 824,010개 삼각형, 내장 이미지 18개. 압축 모델 22,340,952바이트(약 21.31MiB), 25MiB 제한 이내입니다. v76보다 다운로드가 약 2.39MB 늘었으며 실기기 FPS 향상을 주장하지 않습니다.
- 웹 사본만 정점을 0.1mm 단위로 정리했습니다. 새 Blender 편집본은 원래 정밀도를 보존합니다.
- [모델 검증 지표](sources/geumseonggwan-v77/metrics.json)에 원본 해시·모델 크기·충돌 배열 해시를 기록합니다.
- 검증 명령: `node --experimental-strip-types --test tests/world.test.mjs tests/geumseonggwan-exclusive.test.mjs tests/npc-placement.test.mjs tests/geumseonggwan-detail.test.mjs`, `tsc --noEmit`, `vite build --config vite.static.config.ts`.

## 검토 결과와 운영 반영

- 기존 이동·모델·NPC 검사 86개, 새 상세 검사 2개 모두 통과했습니다. 테스트 실행 중 해시 비교에서 Python과 JavaScript의 숫자 직렬화 차이를 발견해 기준 배열을 JavaScript로 정규화했습니다. 실제 충돌 배열은 수정 전후 깊은 비교에서도 일치했습니다.
- TypeScript와 최종 Vite 빌드 성공. Three.js 탐험 청크 크기 경고는 남아 있지만 빌드 실패는 아닙니다.
- Blender에서 전경·정면·처마·실내 4개 렌더를 검토했습니다. `outputs/geumseonggwan-v77`에 PNG를 보관합니다.
- 브라우저 1280×720, 태블릿 크기 1024×768에서 세 보기 버튼, 전체 전경 복귀, 산책 시야 복원을 확인했습니다. 지원 중단된 그림자 옵션 경고를 발견해 설치된 Three.js의 PCF와 radius=2로 수정했습니다.
- 운영 URL: <https://naju-little-walk.vercel.app/>. 연결된 GitHub 생산 브랜치 `codex/bitgaram-place-walks`에 반영하면 Vercel 자동 배포가 실행됩니다. 실제 배포 확인과 화면 캡처는 출력 폴더에 기록합니다.

안드로이드 실기기 GPU·OS 회전 성능은 별도 확인이 필요합니다.
