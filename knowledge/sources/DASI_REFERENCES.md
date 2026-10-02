# 다시초등학교 참고 자료

확인일: 2026-09-08. 대상은 **나주시 다시면 다시로 203, 다시초등학교**입니다. 다시중학교 자료는 사용하지 않았습니다.

## 지도에서 확인한 정보

- [학교 공식 홈페이지](https://najudasi.es.jne.kr/): 학교명과 주소 확인.
- [OSM 학교 부지](https://www.openstreetmap.org/way/963585633): 부지 경계.
- [교사동 윤곽](https://www.openstreetmap.org/way/963585634): 복잡한 다각형을 그대로 투영. 23개 꼭짓점.
- [서쪽 별동 윤곽](https://www.openstreetmap.org/way/963585635): 사각형 건물.
- [지도 원본 API](https://api.openstreetmap.org/api/0.6/map?bbox=126.63865,35.0167,126.6415,35.0186): `dasi-school.osm`에 보관.
- 원점: 위도 35.017517, 경도 126.6400205. 동쪽을 X+, 남쪽을 Z+로 변환. 건물 높이는 지도 자료에 없어 추정했습니다.

지도 출처: © OpenStreetMap contributors, [ODbL 1.0 안내](https://www.openstreetmap.org/copyright). 파생 좌표는 `public/dasi-world.json`과 `dasi-model-provenance.json`에서 확인할 수 있습니다.

## 실제 관찰한 사진

학교의 공개 앨범 목록 대표사진을 열어 건물 형태를 확인했습니다. 상세 게시물에는 로그인이 필요해 접근하지 않았습니다.

| 사진 | 확인한 특징 | 모델에 반영한 범위 |
|---|---|---|
| 2026.06.08 소방합동훈련 | 2층 붉은 벽돌, 흰 창틀, 긴 처마와 기둥, 크림색 상단 보, 원형 표식, 담쟁이, 왼편 둥근 붉은 지붕 | 교사동 외관과 서쪽 별동 지붕의 참고 형태 |
| 2025.10.28 화재대피훈련 | 잔디마당, 황갈색 보도, 파란 박공지붕의 작은 흰 건물, 붉은 코트 | 잔디·보도 재질, 작은 별동과 코트의 단순화된 모양 |
| 2021.06.28 교통안전 챌린지 | 회색 돌 문기둥, 단차 있는 상단과 둥근 장식, 초록 세로 학교명판, 100주년 기념비, 분홍색 계단실형 벽 | 정문 장식과 기념비, 본관 양끝 분홍색 부분 |

- [훈련 사진이 있는 공식 앨범](https://najudasi.es.jne.kr/najudasi_es/na/ntt/selectNttList.do?mi=118994&bbsId=118994&searchType=sj&searchValue=%ED%9B%88%EB%A0%A8)
- [2026년 외관 사진](https://najudasi.es.jne.kr/data/attach_data/hampyeong/najudasi_es/k2board/na/bbs_118994/ntt_1801110048/img_a3ccv2ec2=d0ve4=46vfa=92v53=e382v0301vd34f_v7424.jpg)
- [2025년 마당 사진](https://najudasi.es.jne.kr/data/attach_data/hampyeong/najudasi_es/k2board/na/bbs_118994/ntt_1800830684/img_f172v9b69=fcv6c=44vf0=8dv0f=ae64v102cv5ae6_v8584.jpg)
- [2021년 정문 사진](https://najudasi.es.jne.kr/data/attach_data/hampyeong/najudasi_es/k2board/1186566790_1_1624862228428.jpg)

## 추정과 미확인 부분

### 항공영상으로 보완한 전체 운동장

Esri World Imagery에서 북쪽이 위인 타일 4장을 직접 관찰했습니다. [서비스 출처](https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer), [해당 위치 영상 메타데이터](https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/10/query?geometry=126.6400205%2C35.017517&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=false&f=pjson).

- 촬영일: 2022-10-14. WV02 / Vivid / Vantor. 원본 해상도 0.5m, 위치 정확도 5m로 표시됩니다.
- 타일: `18/103818/223287`, `18/103818/223288`, `18/103819/223287`, `18/103819/223288`.
- 본관 남쪽의 길쭉한 잔디 운동장, 서쪽 별동 아래 주차 공간, 남쪽의 나무 밀집 띠, 남동쪽 파란 지붕 건물과 긴 흰색 지붕 건물을 구분했습니다.
- 예전 모델의 잔디 범위가 주차 공간과 남쪽 수목 구역을 포함하던 부분을 수정했습니다. 경계 좌표는 눈으로 추적한 근사치로 약 5m 이상의 차이가 날 수 있습니다.
- 최근 학교 사진에 나타난 붉은 코트는 동쪽 운동장에 배치했습니다. 2022 항공영상에서는 코트 경계를 확정하지 못했으므로 위치·크기·펜스와 농구대 세부는 추정입니다.
- 남동쪽 건물은 OSM 부지 경계와 일치하지 않습니다. 주변 공간으로 표현했으며 학교 소속·소유를 단정하지 않습니다. 이 구역의 미확인 OSM 경계에 가상의 담장을 만들지 않았습니다.
- 개별 수목·차량·주차선·보행로·화단·국기봉·농구대의 치수는 체험용 세부 표현입니다.

### 남아 있는 추정

- 전체 배치는 OSM 윤곽을 우선했습니다. 현재 모습과의 시점 차이는 있을 수 있습니다.
- 2층 건물의 총 높이 8.3m, 별동 벽 높이 6.2m, 지붕 곡률, 창문 수와 크기는 실측값이 아닙니다.
- 사진 속 둥근 지붕을 OSM의 서쪽 별동과 대응시킨 것은 추론입니다.
- 정문의 동쪽 배치, 문 폭, 기념비 위치, 담장 개구부와 보행로는 추정입니다. 잔디와 수목의 큰 구획만 항공영상으로 보완했습니다.
- 사진에서 보이는 작은 파란 지붕 건물과 코트는 OSM에 윤곽이 없어 별도의 추정 요소로 제작했습니다.
- 상단의 원형 표식은 원본 로고를 복제하지 않고 단순한 원형 장식으로 표현했습니다. 사진만으로 시계인지 확정할 수 없어 시계 바늘은 넣지 않았습니다.
- 지형은 평면입니다. 추가한 1층 복도·교실·도서실, 출입구 위치·가구·책·조명은 실제 실내 자료를 사용하지 않은 가상의 체험 구성입니다. 2층은 외관만 구현했습니다.

## 이미지 사용 방식

원본 사진의 재사용 허용 표시는 확인되지 않았습니다. [학교 저작권보호정책](https://najudasi.es.jne.kr/najudasi_es/iv/indvdlView/selectCpyrhtView.do)을 참고했습니다. 사진은 건축 형태 관찰에만 사용했고, 사이트나 GLB의 텍스처로 포함하지 않았습니다. 벽돌 무늬는 제작 스크립트에서 직접 생성한 패턴이며 GLB에 내장했습니다.
