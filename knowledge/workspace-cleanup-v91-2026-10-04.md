# 파일 정리 v91

사용자 요청에 따라 새 모델 제작보다 먼저 정리했다. 현재 실행 코드의 import 연결을 다시 검사했으며, 추가로 끊어진 실행 파일은 0개였다. 앱에서 직접 import하지 않는다는 이유로 제작 스크립트나 연구 자료를 삭제하지 않았다.

## 삭제 대상

- 이전 업로드 준비 폴더의 모델 복사본 81개. 보존한 `public`, `outputs`, `assets` 모델과 크기·SHA-256이 일치하는 파일만 삭제했다.
- 오래된 배포용 `.tar.gz` 69개. 압축 안에 `dist`와 호스팅 설정만 있고 `.blend`·제작 소스가 없는 것을 검사했다. 현재 Vercel은 GitHub 소스를 빌드한다.
- 다시 생성할 수 있는 빌드·패키지·Python 캐시 5개 묶음. 검증 빌드가 최신 `dist`와 TypeScript 캐시를 다시 만든 것은 정상이다.

총 삭제 용량 **4,815,265,636 bytes = 약 4.82 GB(4.48 GiB)**. 경로·크기·삭제 이유·복사본의 보존 경로는 [삭제 목록](sources/workspace-cleanup-v91.json)에 기록했다.

## 보존과 검증

모든 `.blend`와 `.blend1`, 운영 모델·월드 JSON, 캐릭터 원본과 사용자 미커밋 파일, 사진 자료와 제작 스크립트는 보존했다. 프로젝트 소스를 담은 `work/tablet-site-source.tar`도 남겼다. PowerShell에서 작업 폴더 안의 절대 경로와 링크 여부를 확인했다.

정리 후 TypeScript 검사와 정적 웹 빌드가 통과했다. 운영 코드와 자산은 변경하지 않았다. 영산포 북측 축소는 v90 배포에서 운영 자산 일치까지 확인했다.

재검사: `scripts/audit_workspace_cleanup_v91.py`, `scripts/audit_upload_archives_v91.py`. 삭제는 각 PowerShell 파일의 `-Apply`가 있을 때만 수행한다.
