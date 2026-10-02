# 나주수목원 기초 재현

대상은 사용자가 확인한 산포면 전라남도 산림연구원(다도로 7)이다. 완도수목원 자체를 재현한 것이 아니다. 앞선 질문의 '완도수목원 분원' 표현은 확인되지 않아 명칭으로 사용하지 않는다.

## 확인한 자료

- [공식 위치](https://jnforest.jeonnam.go.kr/content/view.do?menuCd=FOREST007006): 지도 중심 35.0064800, 126.8256689.
- [공식 치유의숲 안내도](https://jnforest.jeonnam.go.kr/content/view.do?menuCd=FOREST003001003): 정문, 원옥제, 방문자센터, 가로수길, 주제 정원, 북쪽 치유센터. 안내도는 축척 측량도가 아니다.
- [항공사진 수록 기사](https://www.emozak.co.kr/news/articleView.html?idxno=12039): 구역별 연구포지, 길 배치, 원형 정원, 온실, 가로수 수형 참고.
- [현장 사진](https://www.ktsketch.co.kr/news/articleView.html?idxno=7656): 메타세쿼이아의 높은 줄기, 녹음, 좁고 긴 길, 벤치와 안내판 참고.
- [OSM 부지](https://www.openstreetmap.org/way/1306096596): 부지 윤곽과 길 중심선. 원본 `sources/arboretum/campus.osm`, 변환 `geometry.json`. © OpenStreetMap contributors · ODbL.

## 실제 자료와 추정 구분

- 실제 지도 기반: 부지 경계, 기록된 주 통행로 6개, 연못 윤곽.
- 사진 참고 추정: 가로수 높이와 간격, 건물 외관·치수·위치, 온실, 벤치, 데크, 원형 정원.
- 가상 보완: 개별 나무 위치·수량, 수종별 색감과 크기 편차. 현장 조사 없이 실제와 동일하다고 주장하지 않는다.
- 산지 치유숲과 실내까지 완성한 모델은 아니다. 현재 단계는 평지 수목원 주 구역을 걷는 기초 모델이다.
- 참고 원본 사진은 웹 배포물에 넣지 않았다.

## 산출물과 성능

- Blender 원본: `outputs/arboretum/naju-arboretum-base-v2.blend` (v1과 기존 수정본 보존).
- GLB 및 압축 전송본: `public/models/naju-arboretum.glb`, `.glb.gz`.
- 산책/연못/줄기/건물 충돌: `public/naju-arboretum-world.json`.
- 나무는 3종 공유 메시 원본으로 제작. 고정 그림자 재사용, 점광원 없이 주광만 사용.
- 774그루, 6개 지도 기반 통행로, 연못, 방문자센터와 연구동 외관 초안, 온실 6동. GLB 약1.8MB로 기본 산책 모델을 구성했다.
- 세부 수형·길 폭은 다음 현장 레퍼런스 검증 때 조정할 수 있도록 생성 스크립트와 Blender를 함께 보존한다.
