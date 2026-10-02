# 수목원 꽃밭·놀이터 보완

작성: 2026-10-01. 안드로이드 태블릿을 주 사용 기기로 설정했다. 실제 기기 조작·성능 검증은 화면 크기 모의 검사와 구분한다.

## 관찰과 제작 범위

2021년 [방문 사진](https://hangamja.tistory.com/1607)의 장미원은 꽃보다 잎·줄기의 비중이 높고, 낮은 생울타리와 밝은 통로, 원뿔형 금속 지지대가 보인다. 같은 자료의 어린이 놀이시설에는 목재 기둥·난간, 녹색 미끄럼틀, 파란 오르기 구조, 밝은 관형 미끄럼틀과 틈이 있는 목재 지붕이 있다. [2024년 여행 기사](https://v.daum.net/v/20241027073357405)에서도 숲속 놀이시설을 확인했다.

이 자료는 현재 실측이나 전체 시설의 정확한 배치 자료가 아니다. 기존 꽃밭 여섯 구획, 꽃 색·수종·개화 밀도, 치수와 식재 좌표는 추정 상태를 유지한다. 자료 사진을 재질로 복사하지 않았다.

기존 웹 화면과 같은 카메라의 Blender 렌더에서 큰 뾰족한 잎, 납작한 꽃잎과 떠 있는 줄기 뿌리를 관찰했다. 새 수정본은 작은 곡면 잎과 복엽, 가지가 있는 장미 줄기, 겹쳐 올라가는 꽃잎, 목재 지붕의 판재와 UV를 보완한다. 기존 나무 수형과 생울타리의 전체 형태는 이번 수정 범위에 포함하지 않는다.

## 원본 보존

- 원본: `outputs/arboretum/naju-arboretum-reference-v15.blend`.
- 초기 보완: `outputs/quality-v61/naju-arboretum-garden-v61.blend`.
- 지붕 UV 보완: `outputs/quality-v61/naju-arboretum-garden-v61-uv.blend`.
- 꽃잎 확대 렌더에서 각진 가장자리와 잘못 향한 면을 발견해 별도 파일 `outputs/quality-v61/naju-arboretum-garden-v61-rounded.blend`에서 다시 수정했다.
- 최종 수정본: `outputs/quality-v61/naju-arboretum-garden-v61-soft.blend`. 꽃잎 끝을 볼록하게 정리하고 중복 정점을 연결해 곡면의 법선이 이어지게 했다.

모든 출력은 기존 파일이 있으면 중단한다. 원본 및 중간 수정본은 덮어쓰지 않는다. 보호 대상의 정점·면·변환, 식생 LOD 쌍, 뿌리 높이와 지붕 범위를 독립 검사한다. 지형·벽·문·시설 위치 및 충돌 JSON은 유지한다.

## 검증과 게시

검사 통과만으로 사진과 완전히 일치하거나 실기기에서 부드럽다고 주장하지 않는다.

- 보호 메시 8,358개의 정점·면·변환이 원본과 일치한다. 수정 대상은 꽃·관목·지붕 7,360개이며, 꽃 뿌리 5,370개를 지면 높이 0.052m에 맞췄다.
- 식생 근거리/원거리 쌍 6,866개는 같은 변환과 전환 거리를 유지한다. 지붕 두 면의 원래 범위를 유지하며 판재 두께 0.027m를 아래쪽에 추가했다. 충돌 JSON 해시는 유지된다.
- [독립 Blender 검사](sources/arboretum/garden-quality-v61-verification.json), [전송 측정](sources/arboretum/garden-quality-v61-transport.json).
- GLB 22,697,564→20,989,336바이트, gzip 9,950,475→9,357,968바이트(약 6% 감소). 공유 메시 삼각형은 259,422→270,716개로 약 4.4% 증가했다. 용량 감소가 실제 프레임 향상을 보장하지는 않는다.
- 꽃밭 도착점의 뿌리 높이, 장미 꽃잎 높이·법선, 목재 지붕 UV·내장 재질, 꽃밭·놀이터 접근 및 보행 회귀 검사 합계 80개 통과. TypeScript와 프로덕션 빌드 성공.
- 1024×768 꽃밭과 844×390 놀이터 화면에서 모델·UI 표시와 콘솔 오류 없음 확인. `outputs/quality-v61/web-flowers-after.png`, `web-playground-844.png`에 기록했다. 데스크톱 브라우저의 화면 크기 검사이며 Android 기기의 OS 회전·멀티터치·성능 검증은 아직 필요하다.
- 최종 전후 렌더: `outputs/quality-v61/roses-before.png`, `roses-soft.png`, `blossom-before.png`, `blossom-soft.png`, `playground-before.png`, `playground-soft.png`.
- 운영 버전 **60** 게시 성공: [수목원 꽃밭](https://naju-little-walk.reinhardt5559.chatgpt.site/?place=naju-arboretum&at=flowers). GitHub 구현 커밋 `0f67dbf`, Sites 게시 소스 `8ff4835187636b1ff7c427f9161ffd5923778e8a`. 동일 소스의 TypeScript·빌드 패키지를 저장·게시했다. 첫 소스 서버 접속은 실패했고 같은 절차 재시도로 성공했다. 공개 범위는 유지했다. 배포 ID `appgdep_6abde968f5b48191b4276688d9ff3a4a`.

## 남은 품질 작업

메타세쿼이아·향나무 등 수종별 수형, 생울타리와 토양 경계, 드들강 노송·산 배경, 캠퍼스 출입구 및 실제 Android 회전·두 손 터치·최대 부하 측정을 [실행 계획](QUALITY_UPGRADE_PLAN.md)에 남긴다.
