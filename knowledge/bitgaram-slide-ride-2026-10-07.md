# 빛가람 돌미끄럼틀 탑승 체험 (2026-10-07)

## 근거 자료와 해석

- 경로: `knowledge/sources/bitgaram/access-v101/navigation-profiles.json`의 `slide_route`. v101에서 위성영상과 현장 사진으로 추적한 덮개 미끄럼틀 중심선(화강암 U자 홈 바닥 높이)이다. 길이 약 93.7 m, 전망대 앞 쉼터 높이 53.64 m에서 전시동 하부 19.21 m까지 내려간다. 고도 자료가 없어 경사는 v101 해석값이다.
- `scripts/build_slide_ride.mjs`가 이 경로를 약 0.7 m 간격으로 줄여 `public/bitgaram-slide-ride.json`을 만든다.

## 가상 요소 (현장 확인 아님)

- 탑승 체험: 실제 미끄럼틀 이용 속도를 잰 자료는 없다. 경사에 따른 가속, 공기·마찰 감속, 끝 12 m 감속 구간을 둔 체험용 계산이다. 최고 약 33 km/h, 전체 약 15초다.
- 착지 매트: 현장 사진에서 확인한 시설이 아니다. 탑승 뒤 내려설 자리를 위해 추가한 가상 소품이다. Blender 원본은 `assets/props/slide-landing-mat.blend`, 웹 모델은 `public/models/props/slide-landing-mat.glb`(가로 2.0 m, 세로 3.1 m)다. 생성 스크립트는 `scripts/build_slide_landing_mat.py`이며, 원본이 있으면 다시 만들지 않고 내보내기만 한다.
- 매트 윗면은 19.26 m다. 미끄럼틀 끝과 같은 높이이고 옆 계단 끝 데크(19.21 m)와 겹쳐 걸어 나갈 수 있다. 걷는 바닥은 `bitgaram-park-world.json`을 고치지 않고 실행 중에 `walk-floor_slide_landing_mat`로 더한다(`lib/slide-ride.ts`).

## 동작

전망대 앞 쉼터 서쪽의 미끄럼틀 입구 3.2 m 안에서 "돌미끄럼틀 타기" 버튼이 뜬다. 입구에서 미끄럼틀 쪽을 보고 걸어 들어가도 출발한다. 앉은 눈높이로 덮개 아치 안을 내려가며 굽은 곳에서 기울고, 속도에 따라 시야가 넓어지고 진동한다. "동작 줄이기" 설정에서는 기울기·진동·시야 변화를 끈다. 매트에서 멈춘 뒤 일어서서 이어서 걷는다.
