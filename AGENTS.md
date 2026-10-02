# 프로젝트 작업 지침

- 한국어로 자연스럽고 간결하게 소통합니다.
- 사용자의 `.blend` 수정본을 생성 스크립트로 덮어쓰지 않습니다.
- 실제 지도 자료와 추정·가상 요소를 `knowledge`에 구분해 기록합니다.
- 도시 모델은 Blender에서 제작·수정하고 GLB로 내보냅니다. Three.js는 그 GLB를 표시하고 탐험 기능을 담당합니다.
- 지형·벽·문 변경 시 해당 장소의 `public/city-world.json` 또는 `public/dasi-world.json` 충돌 정보도 갱신합니다.
- 지도 데이터 출처 표시와 ODbL 안내를 유지합니다.
- 라이브러리, Blender 실행 파일, 임시 압축 파일은 배포에 포함하지 않습니다.
- 이동 기능 변경 시 `node --experimental-strip-types --test tests/world.test.mjs`를 실행합니다.
