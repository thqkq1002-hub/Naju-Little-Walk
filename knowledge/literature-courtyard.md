# 타오르는 강 문학관 마당과 주변 보완

2026-09-08 작업. 기존 편집본을 보존하고 `outputs/yeongsanpo-courtyard.blend`로 새로 제작한다. Blender가 모든 건물·마당 형상을 만들고 Three.js는 GLB 표시와 탐험을 담당한다.

## 직접 확인한 자료

- [전남영상위원회 문학관 로케이션 자료](https://www.jnfilm.or.kr/web_jnfilm/jn_ldbview.php?clmsuid=5079): 정면·앞마당·측면·후면 사진 149483, 149490, 149493, 149487을 확인했다. 페이지의 2025-11-27이 촬영일인지 등록일인지는 확인되지 않았다.
- 마당 특징: 마른 잔디, 흰 자갈과 검은 경계석으로 나눈 굽은 화단, 큰 자연석, 두 줄의 불규칙 디딤돌, 현관 앞 회색 포장과 흰 육각 타일, 세 갈래 나무 지지대, 키 큰 낙엽수, 원목 벤치, 작은 은색 조명, 흰 원통 화분.
- 건물 뒤: 짙은 격자 창, 검은 홈통·선홈통, 낮은 콘크리트 물통과 좁은 보행 공간. 이웃 건물이 가까워 독립된 공원 속 건물처럼 보이지 않는다.
- [Esri World Imagery](https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer): 기존 3328×2560 원본과 문학관 주변 확대 영상을 직접 대조했다. 촬영일은 미상이며 현재 지적도·측량 자료가 아니다.
- [OpenStreetMap](https://www.openstreetmap.org/): 기존 도로·강 좌표와 추가 윤곽을 대조했다. OSM 출처와 ODbL 안내를 유지한다.

## 구현한 부분

- 단순한 직사각 잔디를 남서쪽으로 열린 마당으로 바꾸고, 실제 사진에서 보이는 자갈 화단·자연석·디딤길·조경과 현관 마감을 추가했다.
- 문학관 서쪽 골목 → 남서쪽 마당 입구 → 현관 경로를 연결했다. 지도에 `타오르는 강 문학관 마당`을 추가하고 `?place=yeongsanpo&at=literature-garden`으로 바로 걸을 수 있게 했다.
- 비어 있던 주변에 **새 지붕 35개**를 반영했다. 관찰 후보 33개 중 도로와 가까운 3개는 제외하고 30개를 적용했으며, 문학관에 붙은 이웃 5개를 추가했다. 기존 66개 지붕과 중복되지 않는다.
- 관찰한 주차장, 골목 3개, 녹지·맨땅 구역을 추가했다. 벽체는 위성 지붕 윤곽보다 안쪽에 두고 충돌 정보를 함께 생성한다.

## 추정 및 한계

- 문학관 사진 GPS를 건물 중심으로 사용하던 위치를 위성 지붕 중심에 맞춰 약 8m 조정했다. 이는 육안 정렬이며 측량 좌표 확정이 아니다.
- 마당 경계·길 폭·화단별 치수·식재 위치는 사진과 위성에 맞춘 비례 추정이다. 소유권·법적 필지 경계를 의미하지 않는다.
- 이웃 건물은 지붕 윤곽을 관찰했지만 높이·벽 재료·창·배수관은 추정이다. 모든 집의 실제 입면을 복원했다는 뜻이 아니다.
- 외부 사진·영상·위성 타일을 사이트 텍스처나 배포 파일에 넣지 않는다. 잔디·돌 포장 텍스처는 직접 생성한 재료이고, 글자는 짧은 자체 안내문이다.

## 재생성·검증

```powershell
& '.\work\tools\blender-4.5.13-windows-x64\blender.exe' --background --factory-startup --python scripts/build_yeongsanpo.py -- --only yeongsanpo --output-blend outputs/yeongsanpo-courtyard.blend
& '.\work\tools\blender-4.5.13-windows-x64\blender.exe' --background --python scripts/render_literature_courtyard.py
node --experimental-strip-types --test tests/world.test.mjs
```

직접 수정한 `.blend`에는 재생성 명령을 실행하지 않는다. 다른 출력 이름으로 저장한다. 자동 검증은 마당 왕복 보행, 현관 이동, 자연석 충돌, 주변 건물의 지도 표시·윤곽 일치, 기존 선박 승선·운전과 각 실내 경로를 포함한다. 외관은 Blender 보행 시점·마당 조감도·주변 조감도로 검토한다.

- `scripts/literature_courtyard.py`: 정원·마감
- `scripts/literature_context.py`: 위성 관찰 주변 건물·표면·골목
- `knowledge/sources/literature-context-traces.json`: 후보 33개, 표면 6개, 참고 경로 4개
- `knowledge/sources/literature-close-neighbours.json`: 가까운 이웃 5개
- `public/yeongsanpo-world.json`: 갱신된 바닥·장애물·지도·입구
