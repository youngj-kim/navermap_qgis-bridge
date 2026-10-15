# Naver Map QGIS Bridge

QGIS에서 네이버 지도와 로드뷰를 함께 보며 장소를 찾고, 자동차 경로를 GIS 레이어로 활용하는 연동 플러그인입니다. QGIS 캔버스와 NAVER 지도/로드뷰 위치를 양방향으로 동기화하고, 경로 안내와 이력을 저장하거나 여러 공간 데이터 형식으로 내보낼 수 있습니다.

QGIS 3.34 LTR 이상과 QGIS 4.x를 지원 대상으로 개발합니다. QGIS 3에서는 외부 브라우저 연동 모드, QGIS 4에서는 Dock Widget의 내장 웹 뷰를 사용합니다. 현재 메타데이터 버전은 `0.2.0`이며, 사용자 확인을 마친 실험적 개발 버전입니다.

이 플러그인은 네이버 지도 타일 URL을 추출하거나 QGIS XYZ/TMS 배경지도로 등록하지 않습니다. NAVER Maps JavaScript API v3와 Maps REST API를 사용합니다.

## 현재 기능

현재 개발본에는 카카오 기능 비교와 코드 검토 후 아래 개선을 적용했습니다. 메타데이터는
`0.2.0`을 유지하며, 2026-10-15 사용자로부터 수정본에 이상이 없다는 확인을 받았습니다.

- 탐색창 전체 접기/펼치기와 항상 표시되는 뷰 배치 선택, 일반·위성·위성+지명 전환, 로드뷰 촬영 도로 표시
- QGIS↔NAVER 지도 확대·축소 연동: 지상 거리/픽셀 기준으로 가까운 줌을 선택하며 줌만 변경할 때 로드뷰 위치를 유지
- 경로 취소, API 요청 30초 제한 및 브리지 응답 누락 시 웹 입력창 복구
- 프로젝트 전환 시 현재 경로·입력·진행 요청 초기화, 세션 이력 유지
- 회피 옵션은 하나만 선택하고 경로 유형을 대체. 하이패스와 이륜차는 NAVER Directions 5 미지원으로 새 요청 설정에서 제외

기존 이력 파일은 그대로 읽습니다. 과거 하이패스 값은 보존하되 재조회에 반영하지 않으며,
복수 회피 이력을 입력창으로 불러오면 당시 실제 요청에 사용된 무료 우선을 선택합니다.
`DISTANCE`는 기존 저장값이며 NAVER의 **실시간 편한길**을 뜻합니다.
카카오의 최단거리 옵션과 같은 조건으로 해석하지 않습니다.

하이패스는 **경로 선택 설정**이 공개 Directions 5/15 API에 없습니다. 응답의 안내 코드
`122`(하이패스 전용 톨게이트)는 제공될 수 있으며, 하이패스 관련 정보 전체가 없는 뜻은 아닙니다.
근거: [Directions 5](https://api.ncloud-docs.com/docs/application-maps-directions5),
[Directions 15](https://api.ncloud-docs.com/docs/application-maps-directions15).

검토와 구현 범위는 [기능 비교](docs/kakao-parity-review.md), [구현 기록](docs/implementation-progress.md)을 참고하세요.

- QGIS 메뉴/툴바에서 지도·로드뷰 뷰어 실행
- QGIS 캔버스, NAVER 지도 및 로드뷰 위치의 양방향 동기화와 로드뷰 방향 표시
- 지도·로드뷰 상하/좌우 배치, 분할 비율 조절 및 두 화면 위치 전환
- 로드뷰 촬영일 표시: API가 제공한 값 사용, 정보가 없으면 `촬영일 정보 없음` 표시
- 위도·경도 좌표 입력으로 API 검색 없이 위치 이동 및 경로 지점 지정
- NAVER API HUB 지역 검색 기반 POI/업체/기관명 검색과 NAVER Geocoding 기반 주소 검색
- NAVER Directions 5 자동차 경로를 QGIS 임시 LineString 레이어로 표시
- 출발지, 도착지, 최대 5개 경유지, 경로 안내 포인트 레이어 표시
- 경로 이력 저장/불러오기와 GeoPackage, GeoJSON, Shapefile, GPX 내보내기

출발·경유·도착의 **현재 위치** 버튼은 NAVER 지도 중심 좌표를 사용합니다. 장치의 GPS 위치를 조회하는 기능은 아닙니다. 네이버 지도 타일을 QGIS 베이스맵으로 제공하는 기능도 포함하지 않습니다.

## 검증 상태

- 2026-10-15 사용자 확인: 수정본 사용 후 이상 없음. 사용한 QGIS 버전·브라우저 모드와 개별 시나리오 결과는 별도로 전달되지 않았습니다.
- 수정 과정에서 QGIS 4의 검색·경로 생성과 지도/로드뷰 이동 연동이 사용자 테스트로 정상 작동 확인되었습니다.
- 2026-10-13 검토 수정 후 Python 테스트 67개, 촬영일 12개, 좌표 입력 15개, 외부 브리지 명령 15개와 모의 SDK 레이아웃 48개 시나리오가 통과했습니다.
- 실제 QGIS 3.44.14와 QGIS 4.2.2에서 오프라인 로딩, 레이어 생성, 이력, 파일 저장/재가져오기 및 캔버스 중심 이동을 검증했습니다.
- **별도 확인 필요:** 정확한 QGIS 3.34 런타임과 실제 NAVER API/내장·외부 웹 뷰의 환경별 전체 시나리오 기록. 사용자 확인과 자동·오프라인 검증을 구분하며, 명시되지 않은 환경까지 통과로 확대하지 않습니다.

상세 결과와 남은 시나리오는 [TESTING.md](TESTING.md)를 참고하세요.

안내 분류는 NAVER Directions 코드표를 사용하며 기존 이력은 가져오기와 내보내기 시 분류를 보정합니다. 외부 브리지는 세션 토큰·Host/Origin·JSON Content-Type을 검사하고 Windows에서 포트를 독점합니다. 외부 탭은 플러그인의 열기 버튼으로 실행하세요. 이력 가져오기는 좌표계·지오메트리·범위·안내 개수를 검증하며 실패 시 기존 상태를 복구합니다.

SHP 문자열의 UTF-8 폭이 필드 한도를 넘으면 저장을 중단하고 GPKG/GeoJSON 사용을 안내합니다. 경유지 JSON을 잘라 저장하지 않습니다. 설치 ZIP에는 사용자용 README와 설치 체크리스트만 포함하며 개발 문서·테스트·빌드 도구는 소스에서 관리합니다.

## 개발 구조와 검증

리팩토링된 모듈 책임과 웹 소스 조립 방식은 [REFACTORING.md](REFACTORING.md), 자동/수동 검증 절차는 [TESTING.md](TESTING.md)를 참고하세요. API 키는 로컬 설정에서만 제공하며 테스트는 placeholder와 합성 데이터를 사용합니다.

## 필요한 NAVER Cloud API

지도·주소·경로 기능에는 NAVER Maps 인증 정보, POI/업체/기관명 검색에는 NAVER API HUB 인증 정보를 각각 설정합니다. 현재 구현에서 사용하는 API는 다음과 같습니다.

- Dynamic Map
- Geocoding
- Directions 5
- NAVER API HUB > NAVER 검색 > 지역

자동차 경로 요청은 `maps.apigw.ntruss.com`, 지역 검색 요청은 `naverapihub.apigw.ntruss.com`을 사용합니다. 두 인증 정보를 서로 혼동하지 않도록 주의하세요.

## 인증키 설정

플러그인의 인증 설정 메뉴 또는 기능 실행 시 표시되는 입력창에서 NAVER Maps와 NAVER API HUB의 Client ID / Client Secret을 설정합니다. 값은 QGIS 사용자 설정에 저장됩니다. 실제 키를 소스, README, 테스트 데이터 또는 배포 ZIP에 넣지 않습니다.

환경변수도 지원합니다.

```powershell
$env:NAVER_MAP_CLIENT_ID="YOUR_NAVER_MAP_CLIENT_ID"
$env:NAVER_MAP_CLIENT_SECRET="YOUR_NAVER_MAP_CLIENT_SECRET"
$env:NAVER_API_HUB_CLIENT_ID="YOUR_NAVER_API_HUB_CLIENT_ID"
$env:NAVER_API_HUB_CLIENT_SECRET="YOUR_NAVER_API_HUB_CLIENT_SECRET"
$env:NAVER_MAP_BASE_URL="http://localhost:8083/navermap_qgis_bridge/"
```

NAVER Cloud Platform Application의 서비스 환경 Web URL에는 포트와 경로를 제외한 아래 호스트를 등록하세요.

```text
http://localhost
```

외부 브라우저 bridge의 기본 포트는 `8083`입니다. 사용 중이면 운영체제가 할당한 별도 포트로 시작합니다. 새 세션 토큰이 포함된 주소를 사용하도록 플러그인의 열기 버튼으로 접속하세요. `localhost`라는 호스트 이름 자체가 충돌의 원인은 아닙니다.

콘솔의 `http://localhost` 등록은 실행 포트를 변경해도 그대로 유지합니다. 콘솔 등록 URL과 실제 뷰어 주소(`http://localhost:8083/`)는 구분해야 합니다. [NAVER 공식 인증 문제 해결 안내](https://guide.ncloud-docs.com/docs/maps-troubleshoot)에 따라 콘솔 URL에는 포트와 경로를 넣지 않습니다.

이전 `8082`로 `NAVER_MAP_BASE_URL` 환경변수를 직접 지정한 경우에는 해당 값을 `http://localhost:8083/navermap_qgis_bridge/`로 수정하고 QGIS를 다시 시작해야 합니다. 환경변수는 기본값보다 우선합니다.

## 설치

### ZIP으로 설치

현재 테스트 패키지 설치 후에는 [설치 테스트 체크리스트](docs/install-test-checklist.md)의 묶음별 기대 결과를 확인하세요.

1. 설치용 ZIP을 준비합니다. ZIP의 최상위에는 `navermap_qgis_bridge` 디렉터리 하나만 있어야 합니다.
2. QGIS의 **플러그인 관리 → ZIP으로 설치**에서 파일을 선택합니다.
3. 플러그인을 활성화하고 인증 정보를 설정합니다.

개발 폴더를 심볼릭 링크/정션으로 연결해 사용 중이라면, 개발 소스를 덮어쓰지 않도록 별도의 QGIS 프로필에서 ZIP 설치를 테스트하세요.

### 소스로 설치

QGIS 플러그인 디렉터리에 `navermap_qgis_bridge` 폴더를 복사하거나 심볼릭 링크로 연결합니다. `web` 하위의 HTML, CSS, JavaScript, manifest 및 SVG 리소스도 모두 포함해야 합니다.

Windows 개발용 예시는 다음과 같습니다.

```text
%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\navermap_qgis_bridge
%APPDATA%\QGIS\QGIS4\profiles\default\python\plugins\navermap_qgis_bridge
```

설치 후 QGIS를 다시 시작하고 플러그인 관리자에서 `Naver Map QGIS Bridge`를 활성화합니다.

### 테스트 ZIP 생성

저장소 루트에서 Python 3으로 실행합니다.

```powershell
python tools/build_plugin.py --label test-20261008
```

`metadata.txt`의 버전을 기준으로 `dist/navermap_qgis_bridge-0.2.0-test-20261008.zip`을 생성합니다. 같은 이름의 ZIP은 덮어쓰지 않으므로 재생성할 때는 다른 label을 사용하세요. 생성기는 패키지 구조·Python 문법·내부 import·필수 리소스·ZIP CRC를 검사하고, 로컬 설정·캐시·테스트·개발 의존성은 제외합니다. 테스트 ZIP 생성은 정식 릴리스나 전체 동작 검증을 의미하지 않습니다.

## 업데이트 기록

아래 날짜는 개발 작업 기록이며 별도 릴리스 버전이 아닙니다. 버전의 기준은 `navermap_qgis_bridge/metadata.txt`입니다.

### 2026-10-08 — 리팩토링 기반 및 설치 테스트 패키지

- 기본 localhost 포트를 `8082`에서 `8083`으로 변경하고 내장 웹 뷰의 기본 출처와 외부 bridge 서버 설정을 맞췄습니다.
- 검색/경로, 이력, 내보내기, 레이어 및 캔버스 동기화의 책임을 Python 모듈로 분리했습니다.
- API 요청 생성·응답 해석·요청 수명과 내장/외부 뷰어 메시지 전달을 분리하고 회귀 테스트를 추가했습니다.
- 웹 소스를 HTML 구조, CSS, 기능별 JavaScript로 나누고 두 뷰어 모드가 같은 문서 조립기를 사용하도록 통합했습니다.
- 진단 빌드/동기화 표시는 기본적으로 숨기고, `NAVER_BRIDGE_DEBUG=1`에서 표시하도록 정리했습니다.
- 자동 테스트, QGIS 3.44.14/4.2.2 오프라인 검증 및 설치용 ZIP 생성 도구를 추가했습니다.
- [REFACTORING.md](REFACTORING.md), [TESTING.md](TESTING.md), [AGENTS.md](AGENTS.md)에 구조·검증·작업 지침을 정리했습니다. 실제 NAVER 연동의 최종 수동 검증은 남아 있습니다.

### 2026-09-29 이후 — 검색·동기화·뷰어 개선

- NAVER 좌표 API 처리와 브리지 오류를 수정해 역방향 지도/로드뷰 동기화 및 현재 지도 중심 좌표 입력을 보완했습니다.
- POI 검색 응답과 내장 웹 뷰 전달 경로의 오류를 수정했습니다. 검색·경로·이동 연동은 사용자 테스트에서 정상 작동 확인되었습니다.
- 창 확대/축소와 배치 변경 시 지도/로드뷰가 이전 크기로 남는 문제를 개선하고, 영역 크기에 맞춘 SDK 크기 갱신을 적용했습니다.
- 지도/로드뷰 전환 버튼이 SDK 화면 뒤로 숨는 현상을 수정했습니다.
- 네이버 지도 열기 버튼을 녹색으로 변경하고 로드뷰 촬영일 표시를 추가했습니다. 촬영일은 API가 제공하는 문자열을 사용하며 날짜 선택 기능은 포함하지 않습니다.

### 2026-07-22 — 초기 구현

- `youngj-kim/kakao_qgis-bridge` 구조를 기준으로 NAVER Maps용 QGIS 플러그인 골격을 구성했습니다.
- 카카오 플러그인과 충돌하지 않도록 외부 브라우저 bridge 기본 포트를 `8082`로 설정했습니다.
- QGIS 플러그인 메타데이터를 QGIS3/QGIS4에서 읽을 수 있도록 UTF-8 BOM 없는 `metadata.txt`로 정리했습니다.
- 인증 메뉴를 NAVER Maps `Client ID` / `Client Secret`, NAVER API HUB `Client ID` / `Client Secret` 기준으로 분리했습니다.
- NAVER Maps JavaScript API v3, Dynamic Map, Panorama, Geocoding, Directions 5 호출 흐름을 연결했습니다.
- 좌표 입력 검색은 API 호출 없이 바로 지도/QGIS 중심 이동과 경로 지점 지정에 사용할 수 있도록 처리했습니다.
- NAVER Directions 5 자동차 경로를 QGIS 임시 경로 레이어와 안내 포인트 레이어로 생성하도록 구현했습니다.
- 경로 삭제, 경로 이력 목록, 이력 저장/불러오기, GeoPackage/GeoJSON/Shapefile/GPX 내보내기 기능을 구현했습니다.
- NAVER API HUB 지역 검색(`/search/v1/local`)을 POI/업체/기관명 검색 앞단에 연결하고, 주소 검색은 NAVER Geocoding으로 fallback하도록 구성했습니다.
- 초기 QGIS 4 테스트에서 좌표 검색과 경로 생성을 확인했습니다. 당시 발견한 검색·동기화·뷰어 문제는 이후 작업 기록과 현재 검증 상태를 참고하세요.

## 참고 문서

- NAVER Maps overview: https://api.ncloud-docs.com/docs/application-maps-overview
- NAVER Maps JavaScript API v3: https://navermaps.github.io/maps.js.ncp/docs/
- NAVER Directions 5: https://api.ncloud-docs.com/docs/ai-naver-mapsdirections-driving
- NAVER Geocoding: https://api.ncloud-docs.com/docs/ai-naver-mapsgeocoding-geocode
- NAVER API HUB 지역 검색: https://api.ncloud-docs.com/docs/naver-api-hub-search-local

## License

GPL-2.0-or-later.
