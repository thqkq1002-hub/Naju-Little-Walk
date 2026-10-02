# 금성관 사진·영상 기반 상세 보완

확인·제작일: 2026-09-08. 기존 `outputs/geumseonggwan.blend`는 보존하며 상세본을 `outputs/geumseonggwan-detailed.blend`로 별도 생성합니다. 웹 모델은 `public/models/geumseonggwan.glb`, 이동·충돌 정보는 같은 생성 과정의 `public/city-world.json`입니다.

## 재현 기준과 한계

**수리 전 금성관의 참고 모델**입니다. 현장 실측이나 사진측량 모델이 아니며 현재 공사 상태를 복제한 것이 아닙니다. 정청·익헌·문루 외관, 정청 내부, 마당을 직접 확인한 사진·영상 장면과 공개 도면 썸네일에 맞춰 보완했습니다. 읽을 수 없는 치수나 숨겨진 공간을 정확한 실측 결과처럼 표시하지 않습니다.

중앙 문은 걸어서 들어갈 수 있도록 열린 상태로 표현했습니다. 망화루 상층으로 올라가는 계단 경로, 익헌 방 내부의 숨겨진 구성, 정청 후면 전체의 정확한 입면은 자료로 확인하지 못했습니다. 미세한 단청 그림·기와 개수·곡률·접합부는 직접 만든 근사 표현입니다.

## 직접 확인한 사진

| 출처 | 날짜 확인 | 관찰·반영 |
|---|---|---|
| [국가유산포털 금성관](https://www.heritage.go.kr/heri/cul/culSelectDetail.do?ccbaCpno=1123620370000&pageNo=1_1_1_1), 도록 원본 `2021092716521903.jpg`~`2021092716522102.jpg` | 원본 EXIF **2020-02-18**. 포털 파일명의 2021-09-27과 구분 | 정청 내부 우물마루, 내진 고주 2열, 중심 우물천장과 꽃문양 단청, 둘레 연등 서까래, 들보, 망화루 상층 난간·하층 문 |
| [한국학중앙연구원](https://encykorea.aks.ac.kr/Article/E0011462), 정면·전체 정면 | 설명에 **2009년 촬영** 명시 | 정청 문짝과 고창, 삼각 합각면, 겹처마, 월대·계단 |
| [한국관광공사 열린관광](https://access.visitkorea.or.kr/ms/detail.do?cotId=409a749e-6e4e-410d-803e-c4ab95489110), 경내 드론 2·4·5번 사진 | 촬영일 미확인. 등록 2021-05-07·수정 2025-09-09는 촬영일 아님 | 본관 흙마당과 문루 앞 잔디 구분, 박석 삼도, 울타리로 두른 내삼문터, 서쪽 비석군·담장 |
| [직접 촬영자 드래곤포토](https://dragonphoto.tistory.com/696) | EXIF **2012-07-14**, 게시 2012-08-01 | 중삼문 맞배지붕·목제 문짝, 익헌 뒤쪽 개방 마루, 뒤뜰 은행나무, 자연석 우물과 목재 테두리 |

공식 원본 예: [정청 내부 정면](https://www.heritage.go.kr/unisearch/images/treasure/2021092716521906.jpg), [내부 사선](https://www.heritage.go.kr/unisearch/images/treasure/2021092716521907.jpg), [천장](https://www.heritage.go.kr/unisearch/images/treasure/2021092716522001.jpg), [망화루](https://www.heritage.go.kr/unisearch/images/treasure/2021092716521904.jpg).

## 실제 추출·확인한 영상 프레임

| 영상 | 날짜 구분 | 확인 시점·내용 |
|---|---|---|
| 나주시 공식 채널 [KBC 나주캠페인 볼거리편 1편](https://www.youtube.com/watch?v=J_j0CIXmMg0), [시청 게시물](https://www.naju.go.kr/tour/notice/video?idx=65919&mode=view) | YouTube 업로드 2020-10-07, 시청 게시 2020-12-14. 촬영일 미확인 | 00:19 문짝 철물, **00:20~21 정면·박석길**, **00:22 정면 드론**. 높은 정청과 낮은 익헌, 익헌 안쪽 방·바깥 마루, 중앙·양쪽 계단 |
| 광주MBC [나주 읍성_ 길따라 떠나는 천년고도 나주 여행](https://www.youtube.com/watch?v=ZBVpJn4wsz8), [시청 게시물](https://www.naju.go.kr/tour/notice/video?idx=57913&mode=view) | YouTube 업로드 2015-12-01, 시청 게시 2020-06-23. 촬영일 미확인 | **00:46~48 서측 정측면**. 붉은 합각 세로널, 처마 밑 서까래, 익헌 개방 마루, 돌담·기와 |

영상에서 정청 내부·후면 구조는 확인하지 못해 내부 모델링 근거로 사용하지 않았습니다. 국가유산채널 2013 나주 체험 영상, 2023 가을 홍보 영상과 2017 관광 몽타주도 간격별 프레임을 확인했지만 명확한 금성관 장면을 판독하지 못해 형상 근거에서 제외했습니다.

## 공식 도면과 치수

[2014~2015 정밀실측 사업 자료](https://digital.khs.go.kr/buis/buisDetail.do?bizUid=13898748265494900349&ctptNo=1333604830000&ctptUid=13898859678581301090&nation=&stakeholdersSes=): 문화재청·미추홀건축사사무소. 원본 다운로드는 로그인·이용목적 신청이 필요하여 공개 500×354 썸네일만 확인했습니다.

- [정청 확대 평면도](https://digital.khs.go.kr/record/recordDetailDwg.do?ichDataUid=13897468840669111908&bizId=BIZ201500002192)
- [정청 확대 정면도](https://digital.khs.go.kr/record/recordDetailDwg.do?ichDataUid=13897468840682111909&bizId=BIZ201500002192)
- [지붕 평면도](https://digital.khs.go.kr/record/recordDetailDwg.do?ichDataUid=13897468840630111905&bizId=BIZ201500002192)
- [망화루 정면도](https://digital.khs.go.kr/record/recordDetailDwg.do?ichDataUid=13897468845820212292&bizId=BIZ201500002192), [중문 정면도](https://digital.khs.go.kr/record/recordDetailDwg.do?ichDataUid=13897468845931212301&bizId=BIZ201500002192)

정청은 5칸×4칸, 양끝 정면 칸이 중앙 3칸보다 좁고 양끝 각 2짝·중앙 각 4짝 문입니다. 세 지붕은 따로 구성하며 정청이 높고 앞뒤로 돌출합니다. 이 형태와 [국가유산 디지털 서비스](https://digital.khs.go.kr/heri/heriDetail.do?ctptNo=1123620370000&ctptUid=13898859673312200636)의 겹처마 팔작·익공·2고주 7량 설명을 참고했습니다.

OSM 중앙 외곽은 약 24.24×21.48m이며 지붕 덮임 범위로 해석했습니다. 모델의 기둥 평면 **19.5×16.45m**, 칸 비율·처마 높이는 사진·공개 도면 비례에 맞춘 **추정**입니다. 관광공사 약 320㎡와 국가유산포털 정청 603.19㎡·월대 79.57㎡의 면적 산정 범위 차이는 확인되지 않아 어느 면적도 실측 치수 역산의 절대 근거로 삼지 않았습니다.

## 표현·보존

- 가상 전시 패널·조형물을 상세본에서 제거하고 사진처럼 빈 마루를 표현했습니다. 최초 모델 파일에는 기존 구성을 보존했습니다.
- 단청 꽃문양·기와·돌·목재는 자체 제작한 형상과 색입니다. 사진·영상·워터마크를 텍스처나 배포 자산으로 복사하지 않았습니다.
- 개별 수목·우물·담장·비석·내삼문터 좌표와 높이는 사진 비례 추정이며 정밀 배치도와 다를 수 있습니다.
- © OpenStreetMap 기여자, ODbL 1.0. 원본 5개 건물 윤곽과 도로 출처 표기를 유지합니다.

```powershell
& '.\work\tools\blender-4.5.13-windows-x64\blender.exe' --background --python scripts/build_city.py -- --output-blend outputs/geumseonggwan-detailed.blend --render --render-details
```

같은 상세본이 이미 있으면 생성은 중단합니다. 직접 수정한 원본은 보존하고 생성본만 다시 만들 때 `--replace`를 명시합니다.
