# 빛가람 전망대 접근 지형 — 30m 표고 기반 보강

## 결정과 결과

사용자가 **“30m 자료로 우선 보강하고 정밀도 한계 기록”**을 선택했다. 기존 가우시안 언덕을 공개 Copernicus GLO-30 표면 표고에 맞춘 비대칭 지형으로 교체하고, 승강장·계단·숲길·모노레일·식재·NPC 높이를 함께 갱신했다. 이 결과는 현장 실측 지형이나 준공 도면의 재현으로 표시하지 않는다.

| 기준 | 기존 모델 | 이번 적용 |
| --- | ---: | ---: |
| 상·하부 승강장 바닥 차이 | 9.78m | 약 34.43m |
| 정상 위치의 원자료 표면 표고 | 근거 없음 | 약 79.14m |
| 하부 승강장 주변 좌표의 원자료 표면 표고 | 근거 없음 | 약 44.71m |
| 모노레일 평면 경로 | OSM 508048300 | 같은 좌표 유지 |
| 새 궤도 중심선 길이 | 약 91.80m | 약 98.08m |

79.14m와 44.71m는 표면 표고의 보간 결과다. **정확한 승강장 실측 높이가 아니다.** 정상 자료를 상부 수평 바닥의 기준으로, 하부 주변 자료를 하부 수평 바닥의 기준으로 채택했다. 건물·식생 영향과 자료 시기를 감안해야 한다.

## 실제 자료와 해석의 구분

### 확보한 자료

- [Copernicus GLO-30 공급·해상도·성격 안내](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM): 지면과 나무·건물 등을 포함하는 **DSM**. AWS 공개 2021 배포본을 사용했다. 원 관측은 주로 2010–2015년이며 현재의 토공·시설을 보장하지 않는다.
- [공개 타일 구조와 접근 안내](https://copernicus-dem-30m.s3.amazonaws.com/readme.html): 위경도 1초 간격 GLO-30. 이 지역의 실제 간격은 동서 약 25m, 남북 약 31m다. PixelIsPoint 기준으로 좌표를 읽고 원래 격자 값을 별도로 보존했다.
- [국토환경성평가지도](https://webgis.neins.go.kr/map.do): 2022 국토지리정보원 5m DEM을 이용하지만 공개 조회는 정상의 **50–100m 등급**만 반환했다. 숫자 지면 높이로 사용하지 않았다.
- [한국관광공사 빛가람 전망대 안내](https://korean.visitkorea.or.kr/detail/rem_detail.do?con_type=11300&cotid=9bcea016-ebf7-4cec-ae02-4d67ce2d49fe): 배메산 정상 약 80m 설명을 대략적인 교차 확인에 사용했다. 기사에 혼재하는 100m 수치를 새 지형의 기준으로 쓰지 않았다.
- 기존 OSM 모노레일·숲길·건물·호수 평면 좌표와 출처를 유지했다. © OpenStreetMap 기여자, ODbL.

### 모델에서 해석한 부분

- 모델의 표시 기준 높이는 25.5m다. 동일 DSM에서 호수 경계 표본의 중앙값을 참고해 정한 **로컬 좌표 기준**이며 수위 실측값이 아니다. 따라서 앱의 상부 바닥 y=53.64, 하부 y=19.21은 해발 표고와 구분한다.
- 정상과 하부 승강장은 수평 바닥으로 유지한다. 궤도의 중간 높이는 표고를 따라가고 양 끝에서 승강장 바닥과 객실 바닥이 일치하도록 보정한다. 현재 궤도의 준공 종단선은 확보하지 못했다.
- 기존 전시동의 높이를 표고 위에 다시 더해 지붕이 두 번 높아지지 않도록 건물 바닥과 후면 지형을 정리했다. 궤도·미끄럼틀의 지면 간격과 주변 절토는 모델에서 해석한 시설 상세다.
- 1.5m 표시 격자는 부드러운 지형과 궤도 주변의 간격을 표현하기 위한 보간이다. **원자료의 30m 해상도가 향상된 것은 아니다.**
- 외곽 잔디는 4m 표시 격자로 세분화했다. 기존 공원 윤곽·호수 구멍·수변 폭을 유지하면서 숲길 입구 아래의 지면이 길과 식재 높이를 따라가게 했다. `ground-refinement.json`에 원래 면적과 세분화 후 면적을 대조해 기록한다.
- 중심부 ±220m 밖에서는 기존 주변 지형과 연결하기 위해 300m까지 완만하게 혼합한다. 호수 면과 다른 장소의 모델은 유지한다.
- 나무 뿌리 2,250곳의 높이를 바꾸고, 가까운/먼 수관 쌍은 같은 만큼 이동한다. 원래 수형·배치·크기는 유지했다.

## 구현 파일과 보존

1. `scripts/analyze_bitgaram_terrain_v89.py`: 원자료의 지리 참조 확인, 원래 표고 격자 추출, 기준점 분석.
2. `scripts/bitgaram_terrain_v89.py`: 표고 보간과 시설 높이 해석.
3. `scripts/upgrade_bitgaram_terrain_v89.py`: Blender 지형·시설 높이 변경, GLB 및 보행 정보 동시 내보내기.
4. `public/bitgaram-park-world.json`: 보행 바닥·벽·기둥·궤도 경계·입장 트리거·도착 높이 갱신.
5. `public/npc-placements.json`: 배돌이 발 위치와 시작 높이 갱신.
6. `lib/destinations.ts` / `app/walk-guide.tsx`: 캐시 버전과 표고 자료의 성격·출처·한계 표시.

원본 `outputs/monorail-v83/bitgaram-park-monorail-v83.blend`는 SHA-256으로 보존을 검사했다. 최종 편집본은 **`outputs/terrain-v89/bitgaram-park-glo30-terrain-v89d.blend`**다. 중간 v89·v89b·v89c도 덮어쓰지 않았다. 원본 표고 TIFF, Blender 실행 파일, 생성된 편집본·비교 화면은 배포에 포함하지 않는다.

자료·분석·빌드 기록은 `knowledge/sources/bitgaram/terrain-v89/`에 분리했다. `native-surface-grid.json`의 원래 측정 격자와 `navigation-profiles.json`의 시설 보간 경로를 구분해서 보관한다.

## 검증과 다음 정밀화

- 이동·모노레일·NPC·표고 관련 자동 검사 **95개가 통과**했다. TypeScript 검사와 정적 빌드도 통과했다. `verification.json`에 모델 해시와 원본 보존을 기록했다.
- 계단·숲길 양방향 이동, 승강장 탑승/하차, 객실 바닥 높이, 전망대 자동 입장, NPC 발 위치를 검사했다.
- GLB의 계단·숲길 바닥을 수직 광선으로 조회해 충돌 JSON의 높이와 대조했다. 궤도 아래 지형 간격과 외곽 숲길 입구 아래 잔디 높이도 확인했다.
- 원래 지형의 Color 속성을 새 지형으로 옮겨 검게 표시되는 재질 누락을 방지한다.
- 같은 항공 카메라로 전후를 비교하고, 새 지형의 내려다보는 시점도 렌더링했다. `outputs/terrain-v89/terrain-comparison.png`에 전후 장면과 높이 곡선을 한 페이지로 정리했다.
- 컴퓨터 사용 도구의 초기화가 실패해 실제 배포 화면의 픽셀과 Android 태블릿 조작은 재검증하지 못했다. Blender 화면 검토와 배포 파일 대조는 이 검증과 구분해서 기록한다.

후속 정밀화에는 현재의 국토지리정보원 수치지형도 등고선 또는 5m 이하 지면 DEM, 승강장/궤도 준공 종단도, 현장 기준점이 필요하다. 확보 후 정상·하부·중간 교각의 기준 표고를 같은 수직 기준으로 맞춰 이번 보간과 시설 추정을 교체한다.

## 배포 확인

구현 커밋 `40aca1c7066534f5c85947193e7474d0968f4c0d`의 GitHub 연결 Vercel 자동 배포가 성공했다. [반영된 전망대 주변](https://naju-little-walk.vercel.app/?place=bitgaram-park&v=terrain-v89)의 HTML·앱 실행 파일·지형 GLB 압축 파일·이동 JSON·NPC 배치 JSON을 읽어 로컬 검증본과 대조했고 모두 일치했다. 결과는 `knowledge/sources/bitgaram/terrain-v89/deployment.json`에 기록했다. 이는 배포 파일 검증이며 실제 브라우저 픽셀·태블릿 조작 검증을 대신하지 않는다.

재현 명령의 사용자 인자는 Blender의 `--` 뒤에 둔다. 기존 출력이 있으면 새 편집본 이름을 선택해야 한다.

```powershell
python scripts/analyze_bitgaram_terrain_v89.py
python scripts/prepare_bitgaram_ground_v89.py
blender --background --python-exit-code 1 --python scripts/upgrade_bitgaram_terrain_v89.py -- --shore-refinement
node --experimental-strip-types --test tests/world.test.mjs tests/monorail.test.mjs tests/npc-placement.test.mjs tests/bitgaram-terrain.test.mjs
```
