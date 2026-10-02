# 타오르는 강 문학관 1층 상세 보강

2026-09-08. 사용자가 보낸 1층 화면의 빈 전시벽, 단순한 격자문과 툇마루, 창 너머 파란 배경을 보완했다. Blender에서 제작하고 GLB와 충돌 정보를 함께 갱신했다. 새 편집본은 `outputs/yeongsanpo-literature-ground.blend`이며 이전 모든 `.blend` 파일을 보존했다.

## 실제 자료에서 확인한 형태

[전남영상위원회 로케이션 DB 5079](https://www.jnfilm.or.kr/web_jnfilm/jn_ldbview.php?clmsuid=5079)의 149478·149479·149480·149481·149484·149485·149486 사진을 직접 열어 비교했다. 페이지 표시 날짜 2025-11-27은 촬영일인지 등록일인지 확인되지 않았다.

| 사진 | 관찰 내용 | 반영 |
| --- | --- | --- |
| 149480 | 오른쪽 큰 전시 면, 적갈색 제목, 책 표지·관계 도식·사진 구성, 왼쪽 좁은 패널 | 방 가로보 사이에 맞춘 전시 패널, 책 전시, 자체 제작한 포구 도식, 중앙 칸막이의 좁은 패널과 목재 테두리 |
| 149478·149481·149485 | 가는 세로살과 일부 한지가 있는 미닫이문, 여러 창짝이 이어진 긴 툇마루 | 문살·손잡이·하부 한지·상인방·장식창, 창틀·창턱·짙은 마루와 끝문 |
| 149478·149485 | 창 가까이 처마, 흰 화분, 디딤석, 자갈, 수목 | 실내 창에서 보이는 별도 정원 배경 모형 |
| 149479·149484·149486 | 빼곡한 원목 서가, 계단, 흰 네 칸 유리장, 안내대, 소화기 | 이전 상세본 유지, 새 전시 구역과 함께 검토 |

창 위 흰 벽 띠와 미닫이문 상단 인방 사이를 채웠다. 기존 개구부 `x=-6,0,6`은 열어 두고 닫힌 미닫이문에는 충돌을 추가했다. 창으로 정원 배경을 뚫고 나갈 수 없으며, 기존 현관 출구로 나가면 영산포 외부 맵으로 돌아간다.

## 추정과 새로 제작한 표현

- 전시 제목·짧은 설명·강과 포구 도식은 **자체 제작한 해설 표현**이다. 실제 전시 본문·역사 사진·책 표지를 그대로 복제하지 않았다. 세 개의 낮은 유리 도서 진열장도 전시 밀도를 보완하기 위한 해석이며 현장 가구 수를 확정한 것이 아니다.
- 방 치수·창 개수·패널 폭·가구 위치는 기존 탐험 모델에 맞춘 비례 추정이다. 기존 흰 네 칸 진열장·안내대·소화기는 사진의 계단 가까이 있는 관계보다 모델에서 뒤쪽에 배치되어 있다. 이 위치는 실측 복원이 아니다.
- 창밖 정원은 같은 사진에서 보이는 요소로 제작한 시각적 배경이다. 외부 영산포 맵의 측량 좌표를 그대로 옮긴 공간이 아니며, 실내 맵의 보행 경계와 바닥에는 포함하지 않았다.
- 끝문은 사진에서 관찰한 닫힌 목재 문 표현이다. 화장실 내부나 새 출구를 추가하지 않았다.
- 2층 독서 공간과 계단은 유지했다. 이번 작업은 1층에 집중했으며 100% 실측 재현으로 표시하지 않는다.

## 편집·재생성

- 제작: `scripts/yeongsanpo_literature_ground.py`, 연결: `scripts/yeongsanpo_literature_detail.py`
- 배포: `public/models/yeongsanpo-literature.glb.gz`, `public/yeongsanpo-literature-world.json`
- 편집본: `outputs/yeongsanpo-literature-ground.blend`
- 렌더: `outputs/literature-ground-exhibition.png`, `literature-ground-panels.png`, `literature-ground-veranda.png`, `literature-ground-garden.png`
- 첫 위치: `?place=yeongsanpo-literature&at=exhibit` 또는 `&at=veranda`

```powershell
& '.\work\tools\blender-4.5.13-windows-x64\blender.exe' --background --factory-startup --python scripts/build_yeongsanpo.py -- --only yeongsanpo-literature --output-blend outputs/yeongsanpo-literature-ground.blend
& '.\work\tools\blender-4.5.13-windows-x64\blender.exe' --background --python scripts/render_literature_ground.py
node --experimental-strip-types --test tests/world.test.mjs
```

직접 편집한 `.blend`는 생성 명령으로 덮어쓰지 않는다. 위 명령을 다시 실행할 때는 새로운 출력 이름을 지정하거나, 이번 생성본이 직접 편집되지 않았는지 먼저 확인한다.

## 검증

실제 GLB에 광선을 쏘아 툇마루 창 위·상인방·정원 배경의 닫힘을 확인했다. 세 개 열린 통로, 닫힌 문 충돌, 진열장 보행·지도 배치 차단, 창 통과 방지, 두 새 도착점에서 기존 출구까지의 경로를 테스트했다. 기존 계단·2층 통로·장소 이동 및 선박 기능을 포함한 **59개 테스트**, TypeScript 검사와 정적 빌드가 통과했다. Blender 사람 눈높이 렌더 네 장을 검토하며 웹 브라우저 조작 테스트는 수행하지 않았다.
