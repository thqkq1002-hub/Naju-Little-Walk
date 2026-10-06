# 영산포 맵 북측 배경 축소

사용자가 화면의 빨간 사각형으로 지정한 **강 건너편 넓은 배경 지면**을 제거했다. 선착장·등대·홍어거리·역사갤러리·타오르는 강 문학관과 두 황포돛배는 유지했다.

## 변경 범위

- 기존 `north_bank_background` 지면을 제거했다. 평면 좌표의 북쪽 `z=-230m`를 표시 경계로 정하고, 그 너머의 강물·도로·교량 끝을 Blender에서 잘랐다. 경계에 걸친 입체 메시의 절단면은 닫았다.
- 서쪽 교량은 제거된 배경 지면 쪽으로 허공에 남지 않도록 **기존 수면 지도에 기록된 맞은편 강둑 선**에서 한 번 더 잘랐다. 새 가상 교량이나 가상 강둑은 추가하지 않았다.
- 보행 맵의 남북 범위를 **615m → 530m**로 줄였다. 전체 보기의 중심과 거리를 조정하고 새 모델·이동 자료의 캐시 버전을 `north-crop-v90`로 변경했다.
- 같은 선으로 `public/yeongsanpo-world.json`의 바닥·충돌 윤곽, 도로 좌표, 배의 수면·장애물 범위도 잘랐다. 이동 범위 밖의 잘린 교량 끝으로 갈 수 없게 했다.
- 시작 지점, 모든 도착 지점과 장소, 전시관 출입구, 선착장 계단, 문학관 마당, 배의 크기·정박 위치·승선 정보와 상세 보기 카메라는 변경하지 않았다. 잘리지 않은 바닥·충돌 정보 1,455개를 보존했다.

이는 **사용자가 지정한 화면 범위를 줄이는 편집**이다. 실제 강의 지리적 경계가 바뀌었다는 의미는 아니다. 원본 지도 좌표 자료와 OSM·ODbL 표시는 유지했다. 맵의 표시 범위가 줄어든 것이며, 상세 건물·재질을 유지해 다운로드 크기의 큰 감소를 의미하지 않는다.

## 보존과 재현

원본 `outputs/yeongsanpo-v79/yeongsanpo-detail-v79.blend`를 덮어쓰지 않았다. 최종 편집본은 `outputs/yeongsanpo-crop-v90/yeongsanpo-north-crop-v90b.blend`다. 중간 v90 편집본도 보존했다. 원본 SHA-256과 삭제·절단 객체 목록, 변경 전후 경계, 보존한 이동 자료의 해시를 `knowledge/sources/yeongsanpo-crop-v90.json`에 기록했다.

```powershell
blender --background --python-exit-code 1 --python scripts/crop_yeongsanpo_v90.py -- --bank-repair
node scripts/record_yeongsanpo_crop_v90.mjs
node --experimental-strip-types --test tests/world.test.mjs tests/yeongsanpo-quality.test.mjs tests/yeongsanpo-crop.test.mjs tests/npc-placement.test.mjs
```

이미 새 편집본이 있으면 생성 스크립트는 덮어쓰지 않고 중지한다. 저장된 최종 편집본에서 웹 모델만 다시 내보내려면 Blender 인자 `-- --bank-repair --export-only`를 붙인다. 과거 v79 색·재질·실내 모델의 검사를 유지하고, 의도적으로 바뀐 외부 경계의 기준은 별도 축소 기록과 비교한다.

## 검증

GLB 전체의 최소 북측 좌표, 수면·도로·충돌·보행 경계의 일치, 삭제된 교량 끝의 접근 차단, 남겨 둔 교량 접근 가능 여부를 검사했다. 서쪽 교량 끝이 지도 강둑과 일치하고 그 너머에 교량 메시·보행 바닥이 남지 않은 것도 확인했다. 기존 선착장·전시관 왕복 동선과 배의 출항·조종, NPC 배치 검사를 포함한 **91개 검사**와 TypeScript·정적 빌드가 통과했다. 배포 파일 대조는 `knowledge/sources/yeongsanpo-crop-v90-deployment.json`에 기록한다.

검토 이미지 `outputs/yeongsanpo-crop-v90/yeongsanpo-crop-review.png`는 Blender에서 만든 화면이다. 실제 브라우저 화면과 Android 태블릿 조작 검증과 구분한다. 편집본·Blender 실행 파일·임시 산출물은 배포에 포함하지 않는다.
