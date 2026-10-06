# 나주수목원 지형 분석 원자료

2026-10-03 조사. 운영 모델이나 보행 자료를 변경하지 않는 예비 분석 자료다.

## 파일

| 파일 | 내용 |
| --- | --- |
| `regional-glo90.json` | 250m 간격 99좌표, 조회 URL·원응답·응답 SHA-256·자료 설명 |
| `campus-glo90.json` | 90m 간격 격자 63점 + 현재 명소/시작점 6점 + 기존 가로수길 축 11점 |
| `analysis.json` | 현재 지면 경계 안 29표본의 통계, 명소 표면값, 가로수길 예비 단면, 원본 world SHA-256 |
| `regional-satellite.json` | Esri export 요청·실제 반환 범위·출처·영상 SHA-256. 촬영일 미확인 |
| `regional-satellite.jpg` | 동·남동 산지까지 포함한 연구용 위성 참조 영상 |

고도 출처: [Open-Meteo Elevation API](https://open-meteo.com/en/docs/elevation-api), Copernicus DEM GLO-90, 2021 release. 원자료 해상도 90m. [Copernicus 설명](https://registry.opendata.aws/copernicus-dem/), [DOI](https://doi.org/10.5270/ESA-c5d3d65).

Copernicus·Open-Meteo에 출처를 표시한다. 표면 자료에는 수관·건물 등이 섞일 수 있으며, 최종 노면 높이나 실측 경사로 사용할 수 없다. 43m 간격 가로수길 조회는 길의 단면을 설명하기 위한 추가 표본이며 원자료 해상도를 높이지 않는다.

위성 출처: Esri, Vantor, Earthstar Geographics, and the GIS User Community. 기존 경계·길 출처: OpenStreetMap contributors, ODbL, 2026-09-16. 위성영상을 운영 텍스처로 배포하기 위한 자료가 아니다.

## 재현

프로젝트 루트에서 다음을 실행한다. 네트워크 조회 없이 저장된 JSON을 분석한다.

```powershell
python scripts/analyze_arboretum_terrain.py
python scripts/render_arboretum_terrain_plan.py
```

공개 자료 조회가 필요할 때는 분석 스크립트에 `--fetch --satellite`를 추가한다. 이미 저장된 원응답은 재사용하고 조회 좌표가 다르면 중단한다.

그림 작성은 matplotlib·numpy·Pillow를 사용한다. 이번 로컬 도구는 `work/terrain-analysis-libs`에 있으며 앱 의존성이나 배포 파일에 포함하지 않는다. 출력은 `outputs/arboretum-terrain-plan-2026-10-03/terrain-analysis.png`와 PDF다.

좌표 규칙은 현재 프로젝트와 동일하다: 원점 `[35.00648,126.8256689]`, X 동쪽·Z 남쪽, 단위 m. 현재 로컬 위경도 근사 변환을 사용했다. 실제 제작에서는 자료 좌표계와 고도 기준을 정렬한 뒤 높이를 확정해야 한다.

원자료·그림의 확인값과 후속 제작의 추정값은 [구현 계획](../../../naju-arboretum-terrain-plan-2026-10-03.md)에 구분해 기록했다.
