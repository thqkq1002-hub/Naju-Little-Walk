# 수목원 사진·위성 디테일 보강

## 추가 확인 자료

- [강진호프 현장 블로그, 2023-05-25](https://gangjinhof.tistory.com/710): 정문·경비실·차단기, 길 가장자리 식재, 높은 메타세쿼이아 줄기와 잎 사이 빈 공간 확인. 현재 시설과 다를 수 있다.
- [Esri World Imagery](https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer): 2026-09-16 열람. 이미지 취득일은 확인하지 못했다. 1600×1200 export의 Web Mercator extent를 이용해 지붕과 정원 픽셀을 기존 지리 좌표계로 변환했다. 단순 화면 감각으로 위치를 옮기지 않았다.
- 이전 공식 안내도 및 항공사진과 대조. 실제 배치가 달라진 부분이 있을 수 있어 측량 결과로 취급하지 않는다.

## 반영

- 초안 온실·건물·원형 정원의 추정 배치를 제거하고 위성영상에서 읽은 위치로 수정.
- 연구포지의 줄무늬 식재와 곡선 정원 산책로 추가.
- 메타세쿼이아의 둥근 덩어리 수관을 가지와 작은 잎 묶음으로 교체. 같은 메시를 공유해 중복 저장 억제.
- 정문 경비실·차단기·기둥, 가로수길 가장자리 식재와 바닥 이음매, 연못 가장자리 추가.
- 건물 충돌체와 원형 정원의 지도 이동 위치 갱신.

## 정확도와 보존

지붕 윤곽은 위성 픽셀 수동 판독, 높이·문 위치·수목 치수는 추정이다. 현장 블로그 사진이나 위성 원본은 웹에 재배포하지 않았다. 덩굴터널은 사진에서 확인했으나 위치가 확정되지 않아 이번 모델에 임의 배치하지 않았다.

이전 Blender 원본 보존. 새 원본: `outputs/arboretum/naju-arboretum-reference-v4.blend`.
수동 판독 기록: `sources/arboretum/detail-traces.json`; 좌표 범위: `sources/arboretum/satellite-export.json`.
