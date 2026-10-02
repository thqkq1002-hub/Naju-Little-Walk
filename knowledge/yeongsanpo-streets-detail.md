# 영산포 위성·위치 사진 보강

작업일: 2026-09-08. 최신 외부 편집본은 `outputs/yeongsanpo-streets.blend`이다. 이전 `yeongsanpo-courtyard.blend`와 실내·선박 수정본은 보존한다.

## 반영 내용

- 원본 해상도 위성사진에서 빠진 지붕 30개를 추가했다. 기존 66개와 문학관 주변 35개를 포함해 사진 관찰 지붕은 131개다. OSM 건물은 별도로 유지한다.
- 등대길 뒤쪽과 영산2길 남쪽의 연결 골목 4개를 추적했다. 원본에서 보이는 포장 연결을 따라 2.6~3m의 보수적인 이동 구간을 만들었으며 실제 차도 전체 폭을 측량한 값은 아니다.
- 등대길·선창길·영산3길에 붉은 보도블록, 낮은 연석, 노란 가장자리 표시, 배수구를 만들었다. 교차하는 지도 도로에는 보도를 가로질러 놓지 않는다.
- 도로와 가까운 지붕 모델에 창틀·차양·처마 배수관·간판·실외기를 보강했다. 실제 상호와 위치를 확인하지 못한 상점에는 일반적인 설명 문구를 사용한다.
- 삼화홍어는 KTO 사진의 건물번호 204, 영산포로 204 주소점, 그 점을 포함하는 OSM `way/1000416564`를 연결했다. 흰 정면, 적벽돌 측면, 높은 창, 차양, 건물 모서리 작은 등대와 죽전골목 표시를 모델링했다. 서쪽 정면·북쪽 골목 방향은 지도와 사진을 대조한 해석이며 외벽 치수·개구부 간격은 추정이다.
- 영산포 등대에 삼각 받침, 목재 울타리, 안내 받침과 상부 가로 금속 난간을 추가했다. 선착장 처마 지지대·배관·갑판 끝 이음·구명환도 보강했다.
- 지도에서 `등대길 뒤편 골목`, `죽전골목 · 삼화홍어 외관`으로 이동할 수 있다.

## 확인한 자료와 추정의 경계

| 자료 | 확인한 것 | 확정할 수 없는 것 |
|---|---|---|
| [Esri World Imagery](https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer), z19 원본 3328×2560 | 지붕 평면, 골목의 연결, 주변 배치 | 촬영일 미상. 현재 상태, 실제 벽 위치, 높이, 건물 용도, 출입 권한 |
| [한국관광공사 홍어거리](https://korean.visitkorea.or.kr/detail/ms_detail.do?cotid=4b555ea0-89c7-4656-9ce4-ab04137de0b3), 3346412~3346418 | 보도·점포·죽전골목 장식의 외관 | 개별 촬영일, 실제 치수·현재 영업 상태 |
| [삼화상회 건물 주소점](https://zippoom.com/review/QoX9k-j9bfCwKxfZXM3HDB) | 영산포로 204, 사진 속 204와 일치; 기존 OSM 건물 내부 | 제3자 주소점이므로 국가측량 정확도가 아님 |
| [대한민국역사박물관 영산포 자료](https://archive.much.go.kr/data/01/folderView.do?jobdirSeq=1216) | 2018-08-10 항공·등대 사진, 선착장 시설 관계 | 2019 등록일과 촬영일은 다름. 2026년 현장 상태로 간주하지 않음 |
| [나주시 관광](https://www.naju.go.kr/tour/sights/tour10), KTO 등대 3534204 | 등대 받침·난간·목재 면의 외관 | 개별 촬영일 미확인, 일부 시설 치수 추정 |

이번 추가 지붕 중 박공지붕의 경사, 모든 벽 높이·재료·창문은 추정이다. ㄱ자 지붕은 관찰된 윤곽을 유지하고 벽은 각 변에서 안쪽으로 들여 골목을 침범하지 않게 했다. 모든 사진·위성 타일은 참고 전용이며 배포하지 않는다. 보도·벽·지붕 표면은 Blender에서 직접 만든 재료다. OSM/ODbL 출처 표시는 유지한다.

2018 항공사진에서 확인한 선착장 동서 경사로/계단 전체 배치와 등대 기단의 낮은 단차는 아직 현 모델의 기존 단순화가 남아 있다. 이번에는 등대 받침·난간·외관 마감을 보강했으며, 2026년 현장을 완전히 측량·복제한 결과라고 주장하지 않는다.

## 자료 파일

- `sources/yeongsanpo-round2-roofs.json`: 채택 30개, 제외 3개, WGS84·월드 좌표와 검토 근거.
- `sources/yeongsanpo-round2-lanes.json`: 연결 골목 4개와 폭의 추정 근거.
- `sources/yeongsanpo-samhwa-location.json`: 사진 주소점–OSM 건물 연결.
- [사진 조사 기록](yeongsanpo-street-photo-references.md): 관찰 특징, 날짜, 미확정 시설.

## 재생성·검증

배포용 Git 저장소의 객체 한도는 32MiB다. `scripts/compact_glb.py`는 텍스처를 사용하지 않는 재질의 미사용 UV 좌표만 제거한다. 최종 GLB는 35,127,572바이트에서 27,733,240바이트로 줄었으며, 모든 정점·법선·삼각형·배치·재질·이미지 바이트가 원본과 같은지 비교했다. 모델의 형태나 사진 기반 디테일을 단순화하지 않는다. 편집용 `.blend`는 원래 좌표를 모두 보존한다.

```powershell
& 'work/tools/blender-4.5.13-windows-x64/blender.exe' --background --factory-startup --python scripts/build_yeongsanpo.py -- --only yeongsanpo --output-blend outputs/yeongsanpo-streets.blend
node --experimental-strip-types --test tests/world.test.mjs
node node_modules/typescript/bin/tsc --noEmit
node node_modules/vite/bin/vite.js build --config vite.static.config.ts
& 'work/tools/blender-4.5.13-windows-x64/blender.exe' --background --python scripts/render_yeongsanpo_streets.py
```

직접 수정한 Blender 파일에 위 명령을 덮어쓰지 않는다. 새 출력 이름을 정해 실행한다. GLB와 `public/yeongsanpo-world.json`은 같은 제작 과정에서 내보내 충돌·보도 바닥·지도 지점이 일치한다. 브라우저 자동화 대신 Blender 렌더, 실제 GLB 광선 검사, 경로·승선·운항 테스트와 익명 HTTP 파일 일치 검증을 사용한다.
