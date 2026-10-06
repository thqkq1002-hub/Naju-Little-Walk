# 나주 산책 전체 프로젝트 GitHub 보관

## 범위와 위치

사용자의 전체 업로드 요청에 따라 현재 프로젝트 `D:\새 폴더\나주 도시 만들기`의 제작 자료를 보관한다. PC 전체나 바탕화면 외부 폴더는 포함하지 않는다.

- 공개 앱 소스: <https://github.com/reinhardt7177-lab/naju-little-walk>
- 제작 자료·참고 사진·이전 버전: 별도 **비공개** `reinhardt7177-lab/naju-little-walk-project-archive` 저장소의 Release
- Blender 실행 환경·라이브러리·캐시는 다시 설치할 수 있으므로 설치 방법과 버전을 기록한다.
- 인증키·환경 변수·로그인 설정은 업로드하지 않는다. 현재 로컬 파일은 보존한다.

GitHub 일반 Git은 100MiB 초과 파일을 차단하므로 제작 결과를 Release 패키지로 배포한다. 첨부 파일은 각각 2GiB 미만으로 분할한다. 동일한 SHA-256 파일은 한 번만 넣고 원래 경로별 복원 목록을 제공한다. [대형 파일 안내](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github), [Release 안내](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)

## 구성과 복원

- `manifest.json`: 모든 원래 경로·파일 크기·수정 시간·SHA-256, 패키지별 객체 위치와 제외 내역
- `naju-project-*.zip`: Blender `.blend`·`.blend1`, 캐릭터·렌더·원본 표면·지도·자료·소스·문서를 포함한 제작 결과
- `project-history.bundle`: 패키지에 포함된 Git 브랜치·태그 이력
- `restore_github_project.py`: 비어 있는 폴더에만 복원하며 전체 SHA-256을 검사
- `SHA256SUMS`: 패키지 검사값

모든 Release 첨부 파일을 같은 폴더에 다운로드한 뒤 다음과 같이 실행한다. Python 3.10 이상, 별도 라이브러리 설치는 필요 없다.

```powershell
python restore_github_project.py --packages . --verify-only
python restore_github_project.py --packages . --destination "D:\나주 산책 복원"
```

앱은 복원 폴더에서 Node.js 22.13 이상으로 `npm ci`, `npm run build`를 실행한다. Blender 제작 환경은 4.5.13 LTS다. 이전 `.blend` 전체의 외부 의존성을 실기기로 확인한 것은 아니므로 일부 과거 파일의 시스템 글꼴이나 외부 참조는 별도 확인할 수 있다. 최신 느러지 편집본은 이미지·글꼴을 내부에 묶었다.

과거 압축 파일 3개는 서비스 연결 설정을 제외해 새 보관 사본으로 정제한다. 원본을 덮어쓰지 않으며, 제거한 내부 경로와 원본·사본 해시를 manifest에 기록한다.

## 완료 결과

[비공개 제작 자료 Release](https://github.com/reinhardt7177-lab/naju-little-walk-project-archive/releases/tag/naju-project-v95-20261004)에 업로드와 검증을 완료했다. 저장소가 비공개인 것을 GitHub API로 확인했다.

| 항목 | 결과 |
|---|---:|
| 복원 가능한 프로젝트 파일 | 8,160개, 27,895,509,799바이트(27.90GB) |
| Blender `.blend`·`.blend1` | 246개, 모두 포함 |
| 중복 제거 객체 + Git 이력 | 5,665개, 22,619,843,898바이트 |
| 분할 ZIP | 13개, 8,615,846,103바이트(8.62GB) |
| ZIP와 기본 복원 첨부 파일 | 18개, 8,635,658,214바이트 |

용량은 10진수 GB다. 소스 기준 커밋은 `b6ff71be3c5769f119c7ee557a7527d32248e99c`이며, 해당 시점의 로컬 작업 파일도 경로별로 보관했다. 스냅샷 이후 생성한 최종 배포·보관 검증 문서는 앱 소스와 비공개 보관 저장소에 별도로 기록한다.

압축을 실제로 읽어 5,665개 객체의 내용 SHA-256·크기·ZIP 무결성을 확인했다. 보관 대상 8,160개 경로가 모두 연결되고 Blender 원본이 모두 포함되는 것을 검증했다. 별도의 전체 복원 폴더를 생성한 것은 아니며, `--verify-only` 검사 결과다. [로컬 내용 검사](sources/github-archive-v95/archive-verification.json), [GitHub 첨부 파일 대조](sources/github-archive-v95/remote-verification.json)에 결과를 기록했다. 기본 18개 첨부 파일은 GitHub의 `uploaded` 상태·크기·SHA-256과 모두 일치한다.

추가로 최종 배포 화면과 배포 대조·원격 검증 기록 3개를 Release에 보관했고 검사값도 일치한다. 총 Release 첨부 파일은 21개다. [추가 첨부 파일 대조](sources/github-archive-v95/extra-assets-verification.json)에 기록했다. 보관 대상에서 누락된 제작 파일은 없으며, 과거 압축 파일 3개만 연결 설정을 제외한 사본으로 저장했다. 재설치 가능한 실행 환경과 인증 설정 제외 내역은 manifest에 기록했다. 로컬 원본은 삭제하거나 덮어쓰지 않았다.
