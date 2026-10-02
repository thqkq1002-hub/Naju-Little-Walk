# 다시초 주변 제작 근거

2026-09-08 제작. 범위는 학교 원점 기준 X −285~285m, Z −245~195m, 약 **570×440m**입니다. X는 동쪽, Z는 남쪽입니다. 학교 내부의 기존 자세한 모형을 보존하면서 주변을 새 파일로 제작했습니다.

## 자료에서 확인한 내용

| 자료 | 확인 범위 | 기록 |
|---|---|---|
| [OpenStreetMap 원본](https://api.openstreetmap.org/api/0.6/map?bbox=126.6369,35.0157,126.6432,35.0196) | 학교·주변 건물 윤곽, 다시로·대용길 등 도로 중심선, 다시역·호남선·승강장 외곽, 토지이용 | `dasi-neighborhood.osm` |
| [Esri World Imagery](https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer) | 서·북쪽과 동·남쪽 개별 지붕, 농지·주차장·녹지 | `dasi-west-north-survey.json`, `dasi-east-south-survey.json` |
| [영상 메타데이터](https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/10/query?geometry=126.6400205%2C35.017517&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=false&f=pjson) | 2022-10-14, WorldView-2, Vivid / Vantor, 원본 해상도 0.5m, 위치 정확도 5m | 원점 조회값이며 주변 타일별 촬영일을 각각 확정한 것은 아님 |
| [Koreaimg 다시역 사진 페이지](https://www.koreaimg.com/moongori/view_new2/view.asp?number=78212&siteid=61ee3b670396558c181defe4&view_template=58ede79cb9db689812a5335f) | 1층 벽돌 역사, 갈색 경사지붕, 중앙 박공·흰 처마, 파란 역명판, 유리 출입문·창, 218 주소판 | 정면 사진 EXIF 2014-06-16 14:09:00 |
| 같은 페이지 승강장 사진 | 덮개 없는 상대식 승강장, 자갈, 황색 가장자리, 가선 문형 구조 | 촬영일 미상 |
| 같은 페이지 거리 사진 | 낮은 상가, 기와지붕·평지붕, 전봇대·가공전선 | 정확한 필지와 사진 방향 미확인. 특정 상가의 외관이라고 확정하지 않음 |
| [KB 탑클래스](https://kbland.kr/se/c/426959) | 대용길 26 / 월태리 587-29, 10층 | 실제 층고·건물 높이는 미확인 |
| [KB 태흥주택(중앙)](https://kbland.kr/se/c/554475) | 대용길 12-1 / 월태리 587-106, 5층 | OSM 중앙아파트 명칭과 대조 |
| [집품 남도아파트](https://zippoom.com/부동산/전남-나주시-다시면-남도아파트/p1mcqu) | 월태리 496-1, 4층 | 공공 건축물대장 원문 대신 공개 요약을 확인 |

학교 외관·운동장 사진 근거는 `DASI_REFERENCES.md`를 함께 봅니다. 학교의 2025/2026년 사진과 2022년 영상이 다를 때는 최신 사진에서 확인된 잔디·외관을 우선했습니다.

## 자료를 모형으로 옮긴 방법

- OSM 좌표를 기존 학교와 동일한 원점 `(35.017517,126.6400205)`에서 미터 단위로 변환했습니다.
- 원본 위성 타일을 개별로 보고 지붕 실루엣을 직접 근사했습니다. 사진 합성이나 생성 이미지로 실제 위치를 대신하지 않았습니다.
- OSM 건물과 겹치는 지붕은 지도 외곽을 우선하고 중복 추가하지 않습니다. 제외 후보와 이유는 `public/dasi-neighborhood-world.json`의 `neighborhood.omitted_traces`에 남습니다.
- 사선 촬영 때문에 외벽·그림자가 지붕 실루엣에 섞일 수 있습니다. 일부 겹침은 동일 건물임을 확정하는 근거가 아니므로 보수적으로 제외한 후보도 있습니다.
- 건물은 개별 편집 가능한 Blender 메쉬로 만들고, 같은 제작 과정에서 GLB와 충돌 정보를 출력했습니다.
- 농업용 피복·재배열은 건물로 세우지 않고 얕은 지표면으로 표현했습니다.
- 철로 중심선과 승강장 다각형은 지도 좌표입니다. OSM의 궤간 1.435m 값을 선로에 적용했습니다.
- 학교 남쪽 OSM 진입로 `592336461`과 부지 경계의 교차점에 출입구를 열었습니다. 이전 모형의 추정 동쪽 문기둥을 이 진입로로 옮겼으며, 문기둥 형태는 사진 참고·간격은 추정입니다.

## 추정·미확인 사항

- **실측 복원이나 현재 상태의 완전한 디지털 복제본은 아닙니다.** 가려진 건물, 작은 부속물, 2022년 이후 신축·철거는 빠질 수 있습니다.
- 지붕의 높이·경사, 대부분 건물 층수, 창문·문 위치, 외벽 색, 개별 수목, 전봇대 위치·전선 처짐은 표현을 위한 추정입니다.
- 아파트 3개의 층수는 위 자료로 보완했지만 미터 높이는 층당 2.9m 등을 가정했습니다. 다른 아파트의 층수도 추정입니다.
- 학교 문기둥을 지도상 진입로에 맞춘 것이 사진 속 정문의 정확한 실측 위치임을 뜻하지는 않습니다. 코트 치수·별동 용도도 미확인입니다. 학교 실내는 체험용 구성입니다. 역과 주변 건물은 외관만 제작했습니다.
- 도로 폭, 경계석 높이, 철도 표고·가선 간격·승강장 높이는 실측값이 아닙니다. 지형은 고도 자료 없이 평면으로 유지했습니다.
- 영상 원점의 표기 정확도는 5m이며, 수작업 추적 오차와 건물 기울어짐까지 더해 실제 위치 차이가 더 클 수 있습니다.

## 보존·배포

- 이전 `outputs/dasi-elementary.blend`와 `outputs/dasi-elementary-detailed.blend`, 기존 학교 GLB·JSON은 보존했습니다.
- 새 편집 파일은 `outputs/dasi-neighborhood.blend`, 새 웹 자산은 `public/models/dasi-neighborhood.glb`, 충돌 자료는 `public/dasi-neighborhood-world.json`입니다.
- 지도 출처는 © OpenStreetMap contributors, **ODbL 1.0**입니다. OSM 원본과 파생 좌표를 함께 보관하고 출처 표기를 유지합니다.
- 학교·Koreaimg 사진의 재배포 허가는 확인되지 않았습니다. 사진 자체를 모델 텍스처나 배포 사이트에 포함하지 않았습니다. Esri / Vantor 영상은 형태 관찰 자료로 출처를 표시합니다.
- Blender 실행 파일과 임시 사진, 압축 파일은 배포하지 않습니다.

## 재현

`scripts/build_dasi_school.py`에 `--neighborhood --render`를 전달합니다. 기존 동명 결과가 있으면 중단합니다. 새로 생성한 작업본을 재생성할 때만 `--replace`를 명시하며, 사용자가 편집한 원본을 덮어쓰지 않습니다.
