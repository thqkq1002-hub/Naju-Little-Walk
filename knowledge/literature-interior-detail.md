# 타오르는 강 문학관 실내 상세 보완

2026-09-08. 사용자가 보낸 2층 화면의 단순한 가구·창틀·천장 보와 파란 벽체 틈을 보완했다. 기존 Blender 편집본은 보존하고 `outputs/yeongsanpo-literature-interior.blend`로 별도 저장한다.

## 확인한 사진

[전남영상위원회 로케이션 DB 5079](https://www.jnfilm.or.kr/web_jnfilm/jn_ldbview.php?clmsuid=5079)의 기존 원본 사진을 다시 직접 열어 비교했다. 페이지에 표시된 2025-11-27은 실제 촬영일인지 등록일인지 구분되지 않는다.

| 사진 번호 | 직접 확인한 특징 |
| --- | --- |
| 149482 | 밝은 평천장, 넓고 휜 짙은 목재 보, 높은 가로창, 다다미, 낮은 탁자, X자 등받이 좌식의자, 거의 비어 있는 흰 칸서가, 교차 목재틀과 흰 전구 4개, 벽걸이 에어컨 |
| 149486·149479 | 1층의 빼곡한 짙은 목재 서가, 책장 위 쌓은 책, 좁은 나무계단, 계단 옆 네 칸 도서 진열장·안내대·소화기 |
| 149480 | 검은 목판 천장, 흰 트랙 조명, 직사각형 무늬의 목재 상부 창살, 넓은 미닫이 개구부, 다다미 테두리 |

## 구현

- 2층 벽이 천장보다 약 22cm 낮고 서쪽 바닥이 벽보다 짧던 생성 모델을 수정했다. 벽·천장·바닥이 서로 겹쳐 닫히며 계단 입구는 유지한다.
- 잘게 나뉜 원통 보를 연속된 직사각 단면의 곡선 목재 보로 교체했다. 기둥·가로목·연결부, 나무 마감, 창턱·창 잠금쇠를 추가했다.
- 낮은 원목 탁자 3개와 X자 등받이 좌식의자 12개, 다다미와 직물 테두리, 깊이 있는 흰 칸서가, 목재틀 조명, 에어컨을 제작했다.
- 사진에서 2층 칸서가의 책을 식별하기 어려워 거의 빈 모습으로 표현했다. 책이 빼곡한 갈색 서가는 1층에 구현했다.
- 1층 책장을 깊이 있는 선반·측판·뒤판과 크기가 다른 책들로 보완하고 천장·트랙 조명·격자 상부창·계단 옆 네 칸 진열장 등을 추가했다.
- 실내를 드래그해서 둘러볼 때 안내 글자 전체가 파랗게 선택되는 현상을 줄였다. 입력칸의 텍스트 선택은 유지한다.
- `?place=yeongsanpo-literature&at=reading`으로 2층부터 걸을 수 있다.

## 추정과 표현 범위

방 치수·가구 수·세부 위치·보 곡률·서가 높이는 사진 비례 추정이다. 단일 사진에 보이지 않는 뒤쪽 공간과 창밖 풍경을 측량 복원한 것은 아니다. 창의 밝은 면은 간략한 창유리 표현이며 실제 창밖 영상이 아니다. 책 표지·종이 질감·짧은 전시 도식은 자체 제작했으며 원본 사진과 긴 전시 본문을 배포하지 않는다. 의자 쿠션 재질·색은 사진의 어두운 좌판을 바탕으로 추정했다.

## 파일과 재생성

- 제작: `scripts/yeongsanpo_literature_detail.py`
- 렌더: `scripts/render_literature_interior.py`
- 웹 모델·충돌: `public/models/yeongsanpo-literature.glb.gz`, `public/yeongsanpo-literature-world.json`

```powershell
& '.\work\tools\blender-4.5.13-windows-x64\blender.exe' --background --factory-startup --python scripts/build_yeongsanpo.py -- --only yeongsanpo-literature --output-blend outputs/yeongsanpo-literature-interior.blend
& '.\work\tools\blender-4.5.13-windows-x64\blender.exe' --background --python scripts/render_literature_interior.py
node --experimental-strip-types --test tests/world.test.mjs
```

직접 편집한 Blender 파일은 다른 이름으로 보관하며 생성 명령으로 덮어쓰지 않는다. 실제 GLB의 벽 상단·모서리·창가 바닥에 광선을 쏘아 마감을 확인하고, 계단·독서실 통로·의자 충돌 및 기존 장소 이동을 함께 검증한다.
