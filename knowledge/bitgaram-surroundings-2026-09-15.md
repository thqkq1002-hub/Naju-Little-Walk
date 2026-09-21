# 전망대 공원 주변의 개략 표현

사용자 요청에 따라 상세 전망대 바깥의 빈 공간을 지도 자료로 보완했다.

- 공원 경계: OSM way 508048299. 호수 폴리곤은 제외하고 육지에만 녹지를 표시.
- 저장된 OSM의 footway/path/steps/pedestrian/service 선형을 따라 산책로와 접근로 표시.
- 전망대 앞 주차장 534225871을 포함한 주변 주차장 윤곽과 구획 표시.
- 북쪽 놀이 공간 908801786, 파크골프장 534225867의 실제 지도 윤곽을 서로 다른 바닥색으로 표현.
- 산책로 주변 나무와 일부 벤치는 추정 배치. 놀이기구나 골프 코스의 세부 구성은 자료 없이 만들지 않음.
- 기존 주변 건물·도로·호수는 유지. 회전 지도에도 동일한 주변 녹지와 시설 윤곽을 반영.

포장 폭·주차 구획·나무·벤치는 추정이다. 주변은 배경 표현이며, 기존 상세 산책 구역의 충돌 정보와 이동 범위는 유지한다. `public/bitgaram-park-world.json`의 surroundings에 사용한 지도 ID와 배경 범위를 기록한다. OSM 기여자 표시와 ODbL 안내를 유지한다.

새 원본: `outputs/bitgaram/bitgaram-park-surroundings.blend`. 이전 forest-detail 원본은 보존한다.

회전 지도 최종 원본: `outputs/bitgaram/bitgaram-overview-surroundings-final.blend`.
검증: Blender 렌더 확인, TypeScript 검사 및 Vite 빌드 성공, 기존 이동·모델 테스트 71개 통과. 압축 GLB는 원본과 바이트 단위로 일치한다. 기존 solids/bounds/spawn/arrivals는 변경하지 않았다.
