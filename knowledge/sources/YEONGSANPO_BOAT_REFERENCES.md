# 영산포 선박 디테일 자산

두 파일 모두 새로 만든 Blender 모델이며, 기존 사용자 `.blend`를 열거나 수정하지 않았다. 좌표는 X 좌우 / Y 위 / Z 앞뒤, 선수는 -Z, 가상 수면 Y=0, 갑판 Y=1.10m다. 양측 외곽 중 +X 가운데 난간을 열었다.

## 제원과 추정

| 선박 | 길이 / 폭 | 근거 |
| --- | --- | --- |
| 왕건호 | 29.9m / 9.9m | 2011년 준공 보도 제원 |
| 나주호 | 21.0m / 5.6m | 사진 속 사람·난간·객실 비례에 따른 추정. 실측 제원은 확인하지 못함 |

- 왕건호 보도에는 높이 3.16m, 돛대 포함 18.2m도 기재돼 있으나 기준면과 만재 흘수가 명확하지 않다. 본 모델 수선·갑판·돛대 설치 위치는 추정이다.
- 나주호는 2010년 건조, 49인승 한옥 지붕 목선을 대상으로 했다. 12.5×2.5m는 소형 빛가람호이며 나주호에 적용하지 않았다. 25×5m 목포호, 23×5m 영산강호, 2026년 신조 24t 계획선 21.5×5.4m도 서로 다른 배다.
- 객실 치수, 벤치 길이, 조타실 배치와 상세 계기는 공개 사진으로 확인되는 범위에 맞춘 체험용 추정이다. 조타대는 현대식 원형 핸들·검은 계기대가 사진에 보이는 사실을 바탕으로 재구성했다.
- 목재 무늬·깃발의 간략 전통 문양은 직접 제작한 원본이다. 참고 사진·방송 화면을 모델 텍스처에 복사하지 않았다.

## 확인한 사진

[나주시 공식 선박 소개](https://www.naju.go.kr/tour/recommend/experience/sailboat)

- [나주호 사선 측면](https://www.naju.go.kr/ybmodule.file/smartour/smartour_tour/1380x1/1762913778.jpg): 한옥 객실 하나, 회랑, 중앙 출입문, 청록색 지붕 끝 장식, 노란 방현재.
- [나주호 진행 방향 사진](https://www.naju.go.kr/ybmodule.file/smartour/smartour_tour/1380x1/1762913772.jpg): 넓은 선수·갑판·외부 의자/함.
- [나주호 객실 근접 사진 — 한국관광공사](https://tong.visitkorea.or.kr/cms/resource/83/4103983_image2_1.jpg): 앞 조타창과 핸들, 창호, 난간, 지붕 기와.
- [나주호 후미 좌석](https://www.naju.go.kr/ybmodule.file/smartour/smartour_tour/1380x1/1762913799.jpg): L자 목재 벤치, 환기 루버가 있는 함, 청색 용 깃발.
- [왕건호 객실 2동](https://www.naju.go.kr/ybmodule.file/smartour/smartour_tour/1380x1/1762913785.jpg): 평지붕 객실 두 개와 사이 열린 갑판.
- [왕건호 조타실·난간 근접](https://www.naju.go.kr/ybmodule.file/smartour/smartour_tour/1380x1/1762913790.jpg): 앞유리 와이퍼, 구명환, 적갈색 갑판, 보관함, 계류줄.
- [왕건호 펼친 돛 2장](https://www.naju.go.kr/contents/2362/sailboat5.jpg): 베이지색 세로 돛, 수평 돛살, 목재 난간, 선실 2동. 다른 사진에는 돛을 내린 상태가 있다.

로컬 원본은 `Temp/yeongsanpo-port-refs/photos`에 있다. 파일명의 숫자를 촬영 날짜로 해석하지 않았다.

## 영상에서 실제 확인한 범위

[KBS 「생생3도 — 영산강, 특별한 시간여행을 가다」 2022-08-19 방송](https://www.youtube.com/watch?v=QmWY0WxyYcY). [나주시 공식 영상 목록의 소개](https://www.naju.go.kr/tour/notice/video?idx=108319&mode=view)를 통해 확인했다.

공개 스토리보드의 실제 160×90px 프레임을 5초 간격으로 확인했다. 전체 동영상 재생 및 고해상도 연속 프레임 분석은 하지 않았다. 로컬 파일은 `Temp/boat-detail-refs/QmWY0WxyYcY-frames-0.jpg`부터 `-3.jpg`까지다.

- 약 75~120초: 역사갤러리의 사진 패널과 큰 등대 모형. 현재 모델을 다시 검토할 때 참고 가능.
- 약 135~200초: 일본식 가옥 내부와 정원. 문학관으로 정비되기 이전 방송이므로 현재 전시 배치 근거로 사용하지 않았다.
- 약 205~310초: 강변·선착장·배 위의 회랑, 창틀과 열려 있는 객실, 선실 안/밖에서 보는 시야. 낮은 해상도로 정밀 장비·치수는 판독할 수 없다.

## 제원 출처

- [뉴시스, 2011-07-20 왕건호 준공](https://www.newsis.com/view/NISI20110720_0004856439)
- [남도일보, 2012-02-02 왕건호 제원](https://www.namdonews.com/news/articleView.html?idxno=294718)
- [동아일보, 2016-10-05 나주호 49인승](https://www.donga.com/news/Society/article/all/20161004/80621885/1)

2026년 나주시 공고 제1082호/제1373호의 구형 나주호 매각 목록은 찾았으나 공개 첨부 제원까지 확인하지 못했다. 따라서 이를 실측 확인으로 취급하지 않았다.

## 산출물과 통합

- `najuho.blend`, `wanggeonho.blend`: 미터 단위 원본, 기와·밧줄·좌석·조타대 각각 편집 가능.
- `najuho.glb(.gz)`, `wanggeonho.glb(.gz)`: 이동 선박 각각 별도 모델. 메시·원본 목재 무늬 포함.
- `najuho.json`, `wanggeonho.json`: 로컬 선체 경계, 갑판 바닥, 난간·객실·벤치 충돌, 승선 지점, 조타 지점 및 왕복 경로.
- `*-exterior.png`, `*-deck.png`, `*-helm.png`: Blender 검토 렌더.
- `verify_walk.mjs`: 기존 `lib/world.ts` 이동 함수를 이용한 선실·조타실·후미 갑판 왕복 확인.

`.blend`에서 카메라/조명은 검토용이며 GLB로 내보내지 않았다. 숨김 충돌 프록시는 JSON에만 남기고 GLB에서 제거했다. 선실 천장은 닫혀 있고 지붕을 자동 숨김 처리하지 않는다.
