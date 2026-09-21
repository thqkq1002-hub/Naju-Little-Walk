# 나주 산책 MVP

금성관 주변의 실제 OpenStreetMap 건물 윤곽과 도로 좌표를 **Blender 4.5 LTS**에서 입체로 제작하고, Blender에서 내보낸 GLB를 **Three.js**로 불러와 탐험합니다.

## Vercel 배포

[Vercel 운영 주소](https://naju-little-walk.vercel.app/) · [드들강 산책](https://naju-little-walk.vercel.app/?place=deudeulgang)

2026-09-21 첫 Vercel 배포는 검증한 `dist/client`의 정적 파일 45개를 직접 업로드했습니다. GitHub 자동 배포 연결은 설정하지 않았습니다.

`vercel.json`은 정적 웹 빌드(`npm run build`)와 배포 폴더(`dist/client`)를 지정합니다. GitHub `codex/bitgaram-place-walks` 브랜치의 최신 작업 또는 동일한 정적 빌드 결과를 배포합니다. GitHub 기본 `main` 브랜치는 변경하지 않습니다. 프레임워크 자동 감지 대신 일반 정적 프로젝트 설정을 사용합니다.

`.vercelignore`는 Blender 원본·도구, 참고 자료와 임시 파일을 업로드에서 제외합니다. 완성된 빌드에는 무손실 압축한 `.glb.gz`만 들어가며, 중복된 `.glb`는 포함하지 않습니다. 모델 로더가 gzip 압축을 해제하므로 별도의 `Content-Encoding` 설정은 필요하지 않습니다. `/?place=deudeulgang` 등 기존 장소 주소를 그대로 사용할 수 있습니다.

설정 근거: [Vercel 프로젝트 설정](https://vercel.com/docs/project-configuration).

## 드들강 솔밭과 전체 맵 채색

`/?place=deudeulgang`에서 소나무 숲길, 노래비, 강변과 남쪽 쉼터를 산책할 수 있습니다. OSM 보행로·시설 위치와 Esri 위성영상, 2025년 현장 사진을 참고했습니다. 소나무 280그루의 위치·수형과 세부 시설 치수는 추정입니다. Blender 편집본은 `outputs/deudeulgang/deudeulgang-pine-grove-v3.blend`입니다.

기존 모든 맵과 두 황포돛배의 색감을 Blender에서 조정했습니다. `outputs/palette-v51`에 새 전체 장면 편집본을 보관하고, 기존 정점·이미지·애니메이션을 유지한 채 재질 값만 GLB에 반영합니다. [사진 근거, 제작 방법과 추정 범위](knowledge/deudeulgang-and-map-palette-2026-09-20.md)를 확인하세요.

## 빛가람 장소별 산책 초안

`/?place=bitgaram`의 Blender 조감 화면에서 푯말을 누르면 전망대 주변 공원, 전망실, 한국전력 본사 입구·1층, KENTECH 캠퍼스·1층을 각각 불러옵니다. KENTECH는 OSM 윤곽과 항공·정면 사진을 참고해 확장 강의동, 연구·지원동, RC 생활관, 운동장과 앞마당을 구성했습니다. 높이·도서관 마감과 1층 내부 배치는 추정이며, 근거는 `knowledge/kentech-campus-2026-09-20.md`에 기록합니다.

- Blender 원본: `outputs/bitgaram/*.blend` — 사용자가 직접 수정한 뒤에는 생성 스크립트로 덮어쓰지 않습니다.
- 제작 근거와 재현 범위: [빛가람 제작 기록](knowledge/bitgaram-progress.md)
- 전체 안내 `bitgaram`, 공원 `bitgaram-park`, 전망실 `bitgaram-observatory`, 한국전력 `bitgaram-kepco`, KENTECH `bitgaram-kentech`.

## 영산포 강변 · 홍어거리 · 두 전시관

선착장 맞은편 **상가·주택·창고 20개**의 지붕과 정면·골목 측면을 보강했습니다. 주소점과 사진을 연결한 홍어세상·금성수산, 그 사이 담장 주택, 푸른 박공지붕 창고군을 구분하고 위성사진에서 확인한 **약 168m 주차·진입 포장**을 추가했습니다. `/?place=yeongsanpo&at=riverfront-shops`에서 확인할 수 있습니다. 최신 외부 편집본은 `outputs/yeongsanpo-riverfront.blend`이며 [관찰 근거·추정 범위](knowledge/yeongsanpo-riverfront-detail.md)를 기록했습니다.

문학관 외부의 **목재 경계 울타리·열린 정원 입구·측면 격자창·작은 별채·실외기·홈통·처마기둥**을 보강하고, 박공과 지붕 단차의 빈 벽을 마감했습니다. `/?place=yeongsanpo&at=literature-garden`에서 입구, `&at=literature-side`에서 측면을 확인할 수 있습니다. 당시 외부 편집본 `outputs/yeongsanpo-boundary.blend`는 보존하며 [사진과 경계 추정 범위](knowledge/literature-boundary-detail.md)를 기록했습니다.

영산포 전체는 위성사진에서 누락 지붕 **30개**와 연결 골목 **4개**를 추가하고, 보도블록·배수로·차양·등대 받침·난간을 보강했습니다. 사진의 204 건물번호와 OSM 윤곽을 연결한 **삼화홍어·죽전골목 입구** 외관도 반영했습니다. 거리 보강 당시 편집본 `outputs/yeongsanpo-streets.blend`는 보존합니다. [자료·추정 범위·재생성 기록](knowledge/yeongsanpo-streets-detail.md)을 확인하세요.

문학관 **1층 전시벽·도서 진열장·목재 테두리·촘촘한 미닫이문·툇마루**를 추가 보완하고, 창 위와 천장 연결부를 마감했습니다. 창밖에는 처마·디딤석·화분·정원을 배치했습니다. `/?place=yeongsanpo-literature&at=exhibit`에서 1층 전시방, `&at=veranda`에서 툇마루부터 걸을 수 있습니다. 최신 실내 편집본은 `outputs/yeongsanpo-literature-ground.blend`입니다. [사진 근거·추정 범위·재생성](knowledge/literature-ground-detail.md)을 확인하세요.

2층의 곡선 대들보, 높은 창, X자 좌식의자, 낮은 원목 탁자, 다다미, 흰 칸서가도 유지합니다. `/?place=yeongsanpo-literature&at=reading`에서 2층부터 걸을 수 있습니다. 이전 실내 편집본 `outputs/yeongsanpo-literature-interior.blend`는 보존하며 [당시 확인한 사진과 추정 범위](knowledge/literature-interior-detail.md)를 기록했습니다.

문학관 마당은 공식 사진의 흰 자갈 화단·검은 경계석·자연석·디딤길·나무 지지대·화분·조명을 반영했습니다. 위성에서 관찰한 **주변 지붕 35개**와 주차장·골목을 추가했으며, `/?place=yeongsanpo&at=literature-garden`에서 마당부터 걸을 수 있습니다. 마당 보강 당시 편집본은 `outputs/yeongsanpo-courtyard.blend`로 보존합니다. [마당 출처·추정 범위·재생성](knowledge/literature-courtyard.md)을 확인하세요.

황포돛배 **나주호·왕건호**에 각각 승선해 갑판과 객실을 걸어보고 직접 조종할 수 있습니다. 배 이름의 선착장 버튼 → **승선 / F** → **운전석으로 / F** 순서로 시작하세요. 조종은 **W/S 전진·후진, A/D 방향, Space 제동**이며, `갑판 둘러보기`와 `선착장으로 복귀`를 제공합니다. 정박한 뒤 내릴 수 있습니다.

왕건호는 보도 제원 **29.9 × 9.9m**, 나주호는 **사진 비례 추정 21.0 × 5.6m**입니다. 두 선실의 내부 치수도 사진 참고 추정입니다. 선착장 지반·계단 아래와 문학관 천장 틈을 마감하고, 역사갤러리 연표·7개 입체 상자·검은 격자 천장·옹기·3칸 음식장을 다시 모델링했습니다. [자료와 추정·조작 설명](knowledge/yeongsanpo-detail-and-boats.md)을 확인하세요.

- 최신 편집본: `outputs/yeongsanpo-detail.blend`, `outputs/yeongsanpo-history-detail.blend`, `outputs/yeongsanpo-literature-detail.blend`, `outputs/najuho-detail.blend`, `outputs/wanggeonho-detail.blend`
- 선박 제작: `scripts/build_yeongsanpo_boats.py`; 선박을 먼저 만든 뒤 `scripts/build_yeongsanpo.py`를 실행합니다.
- 조종: `lib/boat-navigation.ts`, 승선과 선내 보행: `lib/boat-fleet.ts`

`/?place=yeongsanpo`에서 황포돛배 선착장과 등대, 영산3길 홍어거리, 역사갤러리·타오르는 강 문학관 외관을 같은 지도에서 둘러봅니다. 두 전시관의 열린 현관으로 걸어 들어가면 별도의 상세 실내가 열리고, 같은 문으로 나가면 원래 거리의 입구 앞으로 돌아옵니다. 문학관은 서재 뒤 계단을 통해 2층 독서공간까지 올라갈 수 있습니다.

- 새 편집본: `outputs/yeongsanpo.blend`, `outputs/yeongsanpo-history.blend`, `outputs/yeongsanpo-literature.blend`
- 제작: `scripts/build_yeongsanpo.py` 및 `yeongsanpo_*.py`
- 실제 자료와 추정의 구분: [구현 기록](knowledge/yeongsanpo-implementation.md), [공식·방문 사진 검토](knowledge/yeongsanpo-photo-references.md)
- 배포: `public/yeongsanpo*-world.json`과 `public/models/yeongsanpo*.glb.gz` (손실 없는 압축)

공개 사진에서 확인한 건축과 전시 특징을 재현했습니다. 방 치수·상점 입면·전시 도식·수면 높이 등은 추정이며 실제 현장의 완전한 스캔은 아닙니다.

## 금성관 입구와 주변 거리 보완

망화루 앞 박석 보행대, 안내판, 자연석 기와담장, 낮은 원목 울타리와 관목 화단, 양쪽 잔디마당을 사진에 맞춰 보완했습니다. OSM의 서측 주차장 윤곽과 통로를 반영했으며, 위성영상에서 해석한 **주변 지붕 37개**를 별도 출처로 추가했습니다. 주변 건물 높이·창문, 주차 차량과 시설물 배치는 추정입니다.

- 최신 편집본: `outputs/geumseonggwan-surroundings.blend` (이전 두 Blender 파일 보존)
- 추가 제작: `scripts/geumseonggwan_surroundings.py`
- 확인 근거: `knowledge/sources/GEUMSEONGGWAN_SURROUNDINGS.md`
- 주변 지붕 관찰: `knowledge/sources/geumseonggwan-surrounding-roofs.json`
- 렌더: `outputs/geumseonggwan-surroundings-overview.png`, `outputs/geumseonggwan-entrance-street.png`, `outputs/geumseonggwan-entrance-aerial.png`

```powershell
& '.\work\tools\blender-4.5.13-windows-x64\blender.exe' --background --python scripts/build_city.py -- --output-blend outputs/geumseonggwan-surroundings.blend --render --render-surroundings
```

## 금성관 사진·영상 상세본

2009년 공식 정면 사진, **2020-02-18 촬영된 국가유산포털 내부 원본**, 나주시·광주MBC 영상의 실제 확인 프레임, 2015년 공개 실측도 썸네일을 대조했습니다. 다섯 칸의 서로 다른 폭과 개별 격자문·고창, 세 팔작지붕의 합각·겹처마·기와, **8개 내진 고주와 우물마루·단청 천장**, 월대·계단, 2층 망화루와 중삼문, 잔디·내삼문터·담장·비석군·우물을 보완했습니다.

- 건축 상세본: `outputs/geumseonggwan-detailed.blend` (최초 `outputs/geumseonggwan.blend` 보존)
- 제작: `scripts/build_city.py`, `scripts/geumseonggwan_detail.py`
- 사진·영상 시각·추정 치수: `knowledge/sources/GEUMSEONGGWAN_PHOTO_VIDEO.md`
- 렌더: `outputs/geumseonggwan-front-detailed.png`, `outputs/geumseonggwan-interior-detailed.png`, `outputs/geumseonggwan-ceiling-detailed.png`

**수리 전 모습의 참고 모델**입니다. 원본 실측도의 치수를 확보하지 못해 기둥 간격·높이·단청 그림·경내시설 좌표는 추정입니다. 중앙 문은 탐험을 위해 열어 두었고, 망화루 상층 계단과 숨겨진 방 내부는 미재현입니다. 사진·영상 원본은 사이트에 배포하지 않습니다.

```powershell
& '.\work\tools\blender-4.5.13-windows-x64\blender.exe' --background --python scripts/build_city.py -- --output-blend outputs/geumseonggwan-detailed.blend --render --render-details
```

## 복암리 고분군과 지도 이동

**복암리고분전시관 내부도 추가했습니다.** 지도에서 전시관을 선택하면 황토색 3호분 절개 모형, 보고서에서 위치를 추적한 41개 매장시설, 유리 난간 관람교량, 토기 진열장, 38석 영상실, 체험 공간과 2층 북카페를 둘러볼 수 있습니다. 계단을 실제로 올라가며 같은 위치의 아래층·위층을 구분합니다.

- 전시관 Blender 최신 마감본: `outputs/bogam-museum-detailed.blend` (기존 원본·finished 파일 보존)
- 사진과 2016·2022년 방송 영상의 실내 관찰을 반영해 엇갈린 돌벽·맞물린 판석 바닥·맞붙인 옹관·천장 접합부·진열장과 차단띠를 보강했습니다. [관찰 근거와 추정 범위](knowledge/bogam-museum-detail.md)를 확인하세요.
- 관람교량 네 코너의 바닥·난간 연결과 막다른 끝부분을 마감했습니다. 계단 입구와 회전 통로는 그대로 걸을 수 있습니다.
- 전시관 렌더: `outputs/bogam-museum-overview.png`, `outputs/bogam-museum-main.png`, `outputs/bogam-museum-bridge.png`
- 제작: `scripts/build_bogam_museum.py`, `scripts/museum_geometry.py`
- 검증 범위와 추정 사항: `knowledge/sources/BOGAM_MUSEUM_REFERENCES.md`

공식 층별 안내는 정밀 평면도가 아닙니다. 현재 내부의 정확한 치수·교량 경로·가구 위치는 확인되지 않아 사진 참고 추정으로 표시했습니다. 화장실·직원 공간·3층 전망대 내부는 미포함입니다.

공식 사진·영상 프레임, 2023년 위성영상, 발굴조사 기록을 대조해 **네 봉분과 주변 360×340m 구역**을 Blender로 제작했습니다. 원형·긴 네모형·넓은 평탄 정상·낮은 봉분의 차이를 반영하고 실제 지도상의 진입로와 농지 구획을 연결했습니다. 현재 실측 3D 모델은 아니며 기록 치수와 추정한 복원 외형을 구분했습니다.

- 편집 가능한 Blender: `outputs/bogam-tumuli.blend`
- 렌더: `outputs/bogam-overview.png`, `outputs/bogam-ground-view.png`, `outputs/bogam-mounds-detail.png`
- 웹 모델·이동 정보: `public/models/bogam-tumuli.glb`, `public/bogam-world.json`
- 제작 스크립트: `scripts/build_bogam.py`
- 사진·영상 확인 범위 및 추정: `knowledge/sources/BOGAM_REFERENCES.md`

**지도로 이동**을 누르면 나주 전체 지도에서 금성관·다시초·복암리 고분군을 선택할 수 있습니다. 현재 장소 탭에서는 열린 지면이나 번호를 눌러 바로 이동합니다. 봉분·건물과 지도 경계는 같은 충돌 정보로 검사합니다. 장소 사이 전체 도시가 연속 모델링된 것은 아닙니다.

```powershell
& '.\work\tools\blender-4.5.13-windows-x64\blender.exe' --background --python scripts/build_bogam.py -- --render
node scripts/build_regional_map.mjs
node --experimental-strip-types --test tests/world.test.mjs
```

기존 `bogam-tumuli.blend`가 있으면 생성 스크립트는 중단합니다. 직접 수정한 파일을 보관한 뒤 생성본만 다시 만들 때 `--replace`를 명시하세요. 다시초·금성관 파일은 열거나 덮어쓰지 않습니다.

## 다시초등학교 추가

현재 학교 체험은 **다시초 주변 약 570×440m**까지 확장했습니다. 위성영상의 지붕·농지·주차 공간과 지도 건물·도로를 대조했고, 다시역 외관·호남선 두 선로·승강장을 추가했습니다. 아래 기존 학교 파일들은 보존했습니다.

- 새 Blender: `outputs/dasi-neighborhood.blend`
- 전체 조감도: `outputs/dasi-neighborhood-overview.png`
- 웹 모형·충돌: `public/models/dasi-neighborhood.glb`, `public/dasi-neighborhood-world.json`
- 주변 제작: `scripts/dasi_neighborhood.py`
- 실제 자료와 추정 범위: `knowledge/sources/DASI_NEIGHBORHOOD_REFERENCES.md`
- 주변 포함 생성: 기존 Blender 명령의 마지막에 `-- --neighborhood --render`를 전달합니다.

2022년 영상과 일부 과거 사진을 기준으로 제작했으며, 현재 모습과 완전히 일치하는 실측 복원은 아닙니다. 주변 건물의 높이·창문·지붕 세부와 평면 지형은 추정입니다.

- 화면 왼쪽의 **다시초등학교**를 누르거나 `/?place=dasi`로 열면 학교 탐험으로 이동합니다. 기본 주소의 금성관 체험은 유지합니다.
- 나주시 다시로 203의 실제 학교 부지와 건물 2개 윤곽을 사용했습니다.
- 공식 학교앨범 사진을 참고해 2층 벽돌 외관, 흰 창틀, 원형 표식, 분홍색 계단실, 둥근 붉은 지붕, 돌 문기둥을 표현했습니다.
- 본관의 열린 문으로 들어가 1층 복도·체험 교실·작은 도서실을 걸어볼 수 있습니다. 실내는 실제 학교 배치와 다른 체험용 구성입니다.
- 뒤집혀 보이던 학교명 간판의 방향과 크기를 수정했습니다. 교실의 책상·의자·칠판, 도서실의 책장·독서 테이블을 추가했습니다.
- 2022-10-14 항공영상과 2025/2026 사진을 대조해 운동장 전체, 서쪽 주차 공간, 남쪽 수목 구역과 길, 코트·농구대, 남동쪽 건물 배치를 보완했습니다.
- 높이·창문 수·개별 수목·정문 위치·코트 치수는 추정입니다. 항공영상으로 잡은 위치도 약 5m 이상 차이 날 수 있습니다. 실측 복원물이 아닙니다.
- 출처 및 확인 범위: `knowledge/sources/DASI_REFERENCES.md`

학교 파일은 기존 금성관 파일과 별도로 관리합니다.

| 파일 | 용도 |
|---|---|
| `outputs/dasi-elementary-detailed.blend` | 실내·운동장·간판 개선본 |
| `outputs/dasi-elementary.blend` | 보존한 최초 학교 원본 |
| `outputs/dasi-overview.png` | 블렌더 조감도 |
| `outputs/dasi-sign-detail.png` | 간판 방향 확인 렌더 |
| `outputs/dasi-classroom.png`, `outputs/dasi-library.png` | 실내 렌더 |
| `public/models/dasi-elementary.glb` | 웹 탐험용 모델 |
| `public/dasi-world.json` | 학교 충돌·위치·출처 데이터 |
| `scripts/build_dasi_school.py` | 학교 모델 재현 스크립트 |
| `scripts/dasi_interior.py` | 출입구·교실·도서실·운동장 세부 구성 |

```powershell
& '.\work\tools\blender-4.5.13-windows-x64\blender.exe' --background --python scripts/build_dasi_school.py -- --render
```

기존 학교 생성본이 있으면 중단합니다. 직접 편집한 파일은 다른 이름으로 보관하고, 생성본 갱신 시에만 `-- --replace --render`를 사용하세요.

`--render-details`를 함께 전달하면 간판과 실내 렌더도 저장합니다. `.blend`에는 개별 편집 가능한 물체를 유지하고, 웹에서는 같은 불투명 재질의 고정 물체를 묶어 그려 렌더링 부담을 줄입니다.

## 체험 범위

- 금성관 주변 약 283 × 256m 구역
- 지도에 등록된 건물 5채: 금성관, 외삼문, 중삼문, 나주곰탕 하얀집, 나주목문화관(원본 지도 이름: 나주시목문화관)
- 금성관 앞마당에서 출발, 출입구 통과, 사진 참고 정청 마루·천장 탐험
- 벽 충돌, 지도 경계, 전체 조망, 위치 지도, 터치 이동

지도 건물 윤곽과 도로 중심선은 실제 좌표입니다. 상세본의 지붕·창호·기둥·마루·박석길은 공식 사진과 영상 및 공개 도면의 비례를 참고했습니다. 높이·세부 치수·수목 위치·도로 폭은 추정입니다. 지형은 평면이며 주변 미등록 건물은 표시하지 않습니다. 실측 3D 복원물이 아닙니다. 최신 참고 범위는 `knowledge/sources/GEUMSEONGGWAN_PHOTO_VIDEO.md`에 기록했습니다.

## 조작

| 조작 | 동작 |
|---|---|
| W A S D | 이동 |
| 마우스 또는 드래그 | 시선 회전 |
| 좌우 방향키 / Q E | 시선 회전 |
| Shift | 빠르게 이동 |
| Esc / 쉬기 | 일시정지 |
| 전체 보기 | 드래그로 회전, 휠로 확대·축소 |
| 처음 위치 | 출발점으로 돌아가기 |
| 지도로 이동 | 나주 지도에서 장소 전환, 현재 장소 지도에서 지점 이동 |

## 파일 구조

- `outputs/geumseonggwan.blend`: 편집 가능한 블렌더 원본
- `outputs/city-overview.png`: 블렌더에서 렌더링한 조감도
- `public/models/geumseonggwan.glb`: **실제로 블렌더에서 내보낸** 브라우저용 모델
- `public/city-world.json`: 같은 제작 과정에서 생성한 충돌·위치 정보
- `scripts/build_city.py`: 지도 → 블렌더 → GLB 재현 스크립트
- `scripts/photo_architecture.py`: 공식 사진에 기반한 금성관 외관 제작
- `knowledge/sources/`: 지도 원본, 좌표 출처, 추정 범위
- `knowledge/MVP.md`: 작업 범위와 다음 단계
- `tests/world.test.mjs`: 출입구 통과·충돌·경계·GLB 검사
- `work/tools/`: 작업 폴더에만 설치한 Blender 휴대용 버전, 배포 제외

## 실행과 재제작

```powershell
npm install
npm run dev
node --experimental-strip-types --test tests/world.test.mjs
npm run build
```

블렌더 원본은 `outputs/geumseonggwan.blend`를 열면 됩니다. 포터블 실행 파일은 `work/tools/blender-4.5.13-windows-x64/blender.exe`입니다.

```powershell
& '.\work\tools\blender-4.5.13-windows-x64\blender.exe' --background --python scripts/build_city.py
```

스크립트는 기존 결과가 있으면 중단합니다. 직접 수정한 `.blend`는 별도 이름으로 저장한 뒤, 생성본을 명시적으로 갱신할 때만 명령 끝에 `-- --replace --render`를 붙이세요. 블렌더에서 벽을 수정하면 웹 충돌 데이터도 같이 갱신해야 합니다.

## 출처

© [OpenStreetMap 기여자](https://www.openstreetmap.org/copyright), ODbL 1.0. 지도 원본과 변경한 좌표 데이터는 `knowledge/sources` 및 `public/city-world.json`에 보관합니다. 공개 배포 시 같은 출처 표기를 유지하세요.

[금성관 국가유산포털](https://www.heritage.go.kr/heri/cul/culSelectDetail.do?VdkVgwKey=12%2C20370000%2C36&pageNo=1_1_1_1)
