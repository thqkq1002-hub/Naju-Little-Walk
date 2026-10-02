# 선착장 맞은편 강변 건물과 포장 보강

2026-09-08. 사용자가 지적한 강변 맞은편의 빈 건물과 넓은 미포장 표현을 대상으로 한다. 외부 편집본은 `outputs/yeongsanpo-riverfront.blend`에 별도로 저장한다. 기존 문학관·거리·선박·실내 Blender 수정본은 보존한다.

## 확인된 자료와 반영 범위

- **평면 배치:** [Esri World Imagery](https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer) z19 원본 3328×2560을 다시 확인했다. 촬영일은 미상이다. 기존 지붕 좌표를 이동하지 않고 `street_west_01`~`11`, `warehouse_01`~`09` 20개에 개별 지붕·외관을 적용한다.
- **거리 외관:** [대한민국역사박물관 2019015288](https://archive.much.go.kr/archiveImage/service.do?idnbr=2019015288), [2019015291](https://archive.much.go.kr/archiveImage/service.do?idnbr=2019015291), [2019015285](https://archive.much.go.kr/archiveImage/service.do?idnbr=2019015285)를 직접 확인했다. 앞 두 항목의 개별 메타데이터에서 2018-08-10 촬영, 공공누리 1유형을 확인했다. 파일번호 2019를 촬영연도로 간주하지 않는다.
- **홍어세상:** 영산포로 205-41, 지도점 [126.7089989,34.999346]이 `street_west_03` 내부다. 1층 유리문과 큰 간판벽, 뒤의 긴 하늘색 박공지붕을 반영한다.
- **금성수산/김지순홍어:** 영산포로 205-13, 지도점 [126.70948,34.999427]이 `street_west_05` 내부다. 2018 사진에서 확인한 금성수산 간판, 살구색·짙은 목재색 전면과 상층 유리창을 반영한다. 현재의 영업·간판 상태를 보장하지 않는다.
- **그 사이 주택:** 상대 위치를 대조한 흰 2층 외벽, 외부 계단, 크림색 담장과 작은 기와 출입문, 대나무를 반영한다. 실내 진입 기능이 없는 관찰용 주택이며 문학관 입구와 다르다.
- **큰 파란 지붕 건물:** 약 3층으로 읽히는 흰 외벽, 작은 창들과 하부 셔터를 적용한다. 창고는 긴 박공지붕과 높은 환기창, 큰 금속문으로 구분한다.
- **포장:** 기존 등대길 OSM 축의 남쪽에 보이는 주차·상가 진입 공간을 별도 수치로 추적했다. 길이 약 168.37m, 포장면 약 3,546.88㎡이며 186개 지붕/OSM 윤곽과 대조한 면적 관통은 0건이다. 기존 등대길과 서쪽 골목에 연결된다. 원래 OSM 도로를 이동하지 않고 포장 하부를 보충한다.

주소·사진·날짜·권한의 자세한 대응은 [거리 사진 조사](yeongsanpo-riverfront-photo-references.md)에 기록했다.

## 수정 이유와 추정 요소

이전 일반 입면 함수는 가장 가까운 도로에서 22m 이내인 한 면에만 창을 만들었다. 실제 상점 앞 주차 공간 때문에 강변 도로에서 물러난 정면과 측면이 생략됐다. 이번 20개는 확인된 북쪽 정면과 골목 측면을 별도로 제작한다.

지붕의 평면 좌표는 관찰 자료지만 **벽 높이, 창 개수·크기, 지붕 경사, 처마·차양·실외기·화분·주차선·차량의 세부 치수와 배치**는 사진 비례 추정이다. 위치가 확인되지 않은 가게는 일반적인 문구를 사용한다. 특히 홍어나라는 사진에서 상대 위치만 확인됐으므로 `_02` 전체를 해당 상점이라고 명명하지 않는다.

`street_west_09`와 OSM `way/1120464648`은 23.66㎡가 부분 중첩한다. 별개의 높은 건물이 지붕을 뚫지 않게 OSM의 겹치지 않는 부분만 낮은 별채로 남긴다. 두 긴 창고 `warehouse_02/03`의 저장 윤곽 중첩은 붙어 있는 복합창고의 경계 해석 한계이며 별도 두 필지라고 주장하지 않는다.

2018 외관과 촬영일 미상 위성자료를 종합한 재구성이며 2026년 현장 전체를 측량한 결과가 아니다. 원본 사진·위성 타일은 참고용으로만 보관하고 웹 모델에 넣지 않는다. OSM/ODbL 표시는 유지한다.

## 제작과 검증

`scripts/yeongsanpo_riverfront.py`가 개별 외관과 포장을 Blender에서 만들고, `scripts/yeongsanpo_outdoor.py`가 기존 지역에 통합한다. `public/yeongsanpo-world.json` 충돌·바닥·지도 도착점은 같은 과정에서 생성한다. 실내·선박 모델은 이번 작업에서 변경하지 않는다.

```powershell
& 'work/tools/blender-4.5.13-windows-x64/blender.exe' --background --factory-startup --python scripts/build_yeongsanpo.py -- --only yeongsanpo --output-blend outputs/yeongsanpo-riverfront.blend
node --experimental-strip-types --test tests/world.test.mjs
node node_modules/typescript/bin/tsc --noEmit
node node_modules/vite/bin/vite.js build --config vite.static.config.ts
& 'work/tools/blender-4.5.13-windows-x64/blender.exe' --background --python scripts/render_yeongsanpo_riverfront.py
```

직접 편집한 `.blend`에는 생성 명령을 덮어쓰지 말고 새 출력 이름을 사용한다. GLB 용량은 `compact_glb.py`에서 바이트가 같은 정점 속성·인덱스 버퍼를 공유해 줄인다. 첫 파일 비교에서 60,579개 속성/인덱스 스트림과 14개 내장 이미지, 모든 정점·법선·재질·오브젝트 배치가 동일함을 확인했다. 기하 단순화나 텍스처 해상도 저하는 하지 않는다.

최종 **65개 테스트**가 통과했다. 정면 유리창의 실제 GLB 방향, 위성 윤곽 유지, 포장 바닥과 화면 높이 일치, 강변·주차 진입축의 왕복 보행, 담장·계단·차량 충돌, 기존 전시관·선박 동선을 확인했다. TypeScript 검사·정적 빌드와 로컬 서버의 파일 일치 검사도 통과했다. 외부 GLB는 **28,101,968바이트**, gzip은 **7,015,084바이트**이며 Blender 파일은 **190,267,998바이트**다. 웹에는 압축 GLB만 포함하고 Blender 도구·원본 사진·작업 파일은 포함하지 않는다.
