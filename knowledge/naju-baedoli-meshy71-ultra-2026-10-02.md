# 배돌이 Meshy 7.1 Ultra 제작

2026-10-02. 사용자가 새 API 키로 배돌이 한 개 제작을 명시적으로 요청했다. 공식 API에서 `meshy-7` 대신 `meshy-7.1`을 권장하므로 7.1의 4K Ultra 형태 생성·4K 텍스처·PBR 재질로 제작했다. 4K는 검토용 원본의 표면 해상도이며 외형 정확도를 보장하는 조건은 아니다.

## 상태

**생성 성공, GLB·Blender 검증 완료.** 작업 `01a0fbf2-9902-769f-8095-6cafbfff622d` 한 건만 제출했고 `SUCCEEDED / 100%`를 확인했다. 잔액은 1,100 → 1,065로 실제 차감은 **35 Meshy API 크레딧**이다. 충전이나 원화 결제는 대신 실행하지 않았다. 키는 명령 프로세스 환경에서만 사용하고 소스·지식 문서·설정 파일에 저장하지 않았다. 기존 T2 샘플과 3D Jutsu 샘플을 대체하거나 삭제하지 않았다. 운영 앱의 기존 캐릭터도 유지했다.

이전 6크레딧 계정으로는 미제출 상태였으나, 새 키로 연결된 계정에서 잔액을 확인해 진행했다. 힉스필드 작업이나 힉스필드 크레딧 차감이 아니다.

## 제작 설정

- 실행 스크립트: `scripts/meshy_baedoli_ultra.py`
- 안전한 설정 명세: `assets/npc/meshy71-ultra-20261002/generation-plan.json`
- 참조: `assets/npc/higgsfield-rebuild-20261002/references/baedoli-front.png`
- 모델: `standard / meshy-7.1`
- `geometry_resolution: 4k`, `texture_resolution: 4k`
- `should_texture: true`, `enable_pbr: true`
- 원형 세부를 보존하기 위해 `should_remesh: false`; 생성 후 Blender에서 별도 운영용 단순화를 검토한다.
- 원본 참조 외형을 유지하도록 `image_enhancement: false`.
- 기존 포즈 유지, 리깅·애니메이션 미포함.

제출 전에 잔액을 다시 검사하고 35크레딧 미만이면 유료 요청을 보내지 않는다. 제출 결과가 불명확하면 중복 작업을 만들지 않는다. 원본 모델은 별도 경로에 보존한다. API 키와 서명 URL은 설정 명세·Git·배포에 저장하지 않는다.

가격: 채색 30 + Ultra 형태 5 = **35 Meshy API 크레딧**. [공식 요금표](https://docs.meshy.ai/en/api/pricing), [모델·형태 생성 옵션](https://docs.meshy.ai/en/api/image-to-3d).

## 결과 파일

모두 `assets/npc/meshy71-ultra-20261002/`에 저장했다.

| 파일 | 내용 |
| --- | --- |
| `baedoli-meshy71-original.glb` | Meshy 원본, 수정하지 않음 |
| `baedoli-meshy71-review.glb` | 높이 1.2m·발바닥 Z=0으로 정규화, 렌더 도우미 제외 |
| `baedoli-meshy71-review.blend` | 텍스처를 내장한 편집용 Blender 파일 |
| `baedoli-meshy71-front.png` | 실제 모델 정면 렌더 |
| `baedoli-meshy71-three-quarter.png` | 실제 모델 사선 렌더 |
| `baedoli-meshy71-back.png` | 실제 모델 뒷면 렌더 |
| `generation-record.json` | 작업 ID·설정·성공 상태·전후 잔액 |
| `blender-verification.json` | 메시·텍스처·높이·원본 해시 검사 |

## 검증과 운영 제한

- 원본 GLB 헤더·내장 버퍼를 검사하고 Blender에서 실제로 읽어 렌더했다. 외부 텍스처 경로에 의존하지 않는다.
- 메시 1개, 재질 1개, 삼각형 **542,568개**. 검토용 GLB는 **31,836,144바이트**다.
- 색상·노멀은 4096×4096, 금속/거칠기는 2048×2048이다. 모든 텍스처가 4K인 것은 아니다.
- 노란 배 얼굴, 주황 밀짚모자, 파란 목수건, 배를 든 포즈와 엄지 포즈가 반영됐다. 손가락 윤곽 일부와 신발 표면은 수작업 정리가 필요하다.
- 단일 정면 이미지를 참조했다. 뒷면은 AI가 추정한 형태이며 공식 캐릭터 후면 자료로 검증하지 않았다.
- 리깅·애니메이션 없는 정적 모델이다. 모바일 산책 앱에 넣기 전 별도 경량화·움직임 작업이 필요하다. 현재 운영 파일 교체·배포는 하지 않았다.
- 기존 사용자 `.blend` 수정본을 덮어쓰지 않았다. 검토 파일은 별도 이름으로 생성했다.
