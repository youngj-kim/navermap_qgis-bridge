# Naver Map QGIS Bridge

QGIS 3.34 LTR 이상과 QGIS 4.x를 함께 고려한 NAVER Maps 연동 플러그인입니다. QGIS Dock Widget 안에서 NAVER Dynamic Map과 거리뷰(Panorama)를 표시하고, QGIS 캔버스 중심 좌표와 지도/거리뷰 위치를 양방향으로 동기화합니다.

이 플러그인은 네이버 지도 타일 URL을 추출하거나 QGIS XYZ/TMS 배경지도로 등록하지 않습니다. NAVER Maps JavaScript API v3와 Maps REST API를 사용합니다.

## 현재 기능

- Plugin Builder 없는 QGIS 플러그인 구조
- QGIS 메뉴/툴바 액션 등록
- Dock Widget 내부 `QWebEngineView` 지도 뷰어
- QGIS 3 환경용 외부 브라우저 연동 모드
- QGIS 캔버스 중심 좌표를 EPSG:4326으로 변환해 NAVER 지도/거리뷰로 전달
- NAVER 지도 이동 및 거리뷰 위치 이동을 QGIS 캔버스에 역방향 반영
- NAVER API HUB 지역 검색 기반 POI/업체/기관명 검색과 NAVER Geocoding 기반 주소 검색
- NAVER Directions 5 자동차 경로를 QGIS 임시 LineString 레이어로 표시
- 출발지, 도착지, 최대 5개 경유지, 경로 안내 포인트 레이어 표시
- 경로 이력 저장/불러오기와 GeoPackage, GeoJSON, Shapefile, GPX 내보내기

## 개발 구조와 검증

리팩토링된 모듈 책임과 웹 소스 조립 방식은 [REFACTORING.md](REFACTORING.md), 자동/수동 검증 절차는 [TESTING.md](TESTING.md)를 참고하세요. API 키는 로컬 설정에서만 제공하며 테스트는 placeholder와 합성 데이터를 사용합니다.

## 필요한 NAVER Cloud API

NAVER Cloud Platform의 같은 Application에서 아래 API를 활성화하세요.

- Dynamic Map
- Geocoding
- Reverse Geocoding
- Directions 5
- NAVER API HUB > NAVER 검색 > 지역
- Static Map은 현재 필수는 아니지만 함께 켜두어도 됩니다.

Maps 공통 가이드의 새 API 호스트(`maps.apigw.ntruss.com`)와 헤더 인증 방식을 기준으로 구현했습니다.

## 인증키 설정

플러그인 최초 실행 시 Client ID와 Client Secret을 각각 입력합니다. 값은 QGIS 사용자 설정에 저장됩니다.

환경변수도 지원합니다.

```powershell
$env:NAVER_MAP_CLIENT_ID="YOUR_NAVER_MAP_CLIENT_ID"
$env:NAVER_MAP_CLIENT_SECRET="YOUR_NAVER_MAP_CLIENT_SECRET"
$env:NAVER_API_HUB_CLIENT_ID="YOUR_NAVER_API_HUB_CLIENT_ID"
$env:NAVER_API_HUB_CLIENT_SECRET="YOUR_NAVER_API_HUB_CLIENT_SECRET"
$env:NAVER_MAP_BASE_URL="http://localhost:8082/navermap_qgis_bridge/"
```

NAVER Cloud Platform Application의 서비스 환경 Web URL에는 아래 출처를 등록하세요.

```text
http://localhost:8082
```

카카오 플러그인과 충돌하지 않도록 기본 포트는 `8082`입니다.

## 설치

QGIS 플러그인 디렉터리에 `navermap_qgis_bridge` 폴더를 복사하거나 심볼릭 링크로 연결합니다.

Windows 개발용 예시는 다음과 같습니다.

```text
%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\navermap_qgis_bridge
%APPDATA%\QGIS\QGIS4\profiles\default\python\plugins\navermap_qgis_bridge
```

설치 후 QGIS를 다시 시작하고 플러그인 관리자에서 `Naver Map QGIS Bridge`를 활성화합니다.

## 2026-07-22 작업 메모

- `youngj-kim/kakao_qgis-bridge` 구조를 기준으로 NAVER Maps용 QGIS 플러그인 골격을 구성했습니다.
- 카카오 플러그인과 충돌하지 않도록 외부 브라우저 bridge 기본 포트를 `8082`로 설정했습니다.
- QGIS 플러그인 메타데이터를 QGIS3/QGIS4에서 읽을 수 있도록 UTF-8 BOM 없는 `metadata.txt`로 정리했습니다.
- 인증 메뉴를 NAVER Maps `Client ID` / `Client Secret`, NAVER API HUB `Client ID` / `Client Secret` 기준으로 분리했습니다.
- NAVER Maps JavaScript API v3, Dynamic Map, Panorama, Geocoding, Directions 5 호출 흐름을 연결했습니다.
- 좌표 입력 검색은 API 호출 없이 바로 지도/QGIS 중심 이동과 경로 지점 지정에 사용할 수 있도록 처리했습니다.
- NAVER Directions 5 자동차 경로를 QGIS 임시 경로 레이어와 안내 포인트 레이어로 생성하도록 구현했습니다.
- 경로 삭제, 경로 이력 목록, 이력 저장/불러오기, GeoPackage/GeoJSON/Shapefile/GPX 내보내기 기능을 구현했습니다.
- NAVER API HUB 지역 검색(`/search/v1/local`)을 POI/업체/기관명 검색 앞단에 연결하고, 주소 검색은 NAVER Geocoding으로 fallback하도록 구성했습니다.
- QGIS4에서 좌표 기반 검색과 경로 생성은 동작 확인했습니다.
- 확인 필요: QGIS4에서 POI명 검색(`서울역`, `용산역`)과 경로 이력 불러오기는 아직 현장 테스트에서 실패가 재현되어, 다음 작업에서 QGIS 메시지 로그와 API HUB 응답을 기준으로 추가 디버깅이 필요합니다.
- UI 이슈: 지도/로드뷰 분할 표시가 QGIS3/QGIS4 공통으로 깨지는 현상이 있으며, 다음 작업으로 분리했습니다.

## 참고 문서

- NAVER Maps overview: https://api.ncloud-docs.com/docs/application-maps-overview
- NAVER Maps JavaScript API v3: https://navermaps.github.io/maps.js.ncp/docs/
- NAVER Directions 5: https://api.ncloud-docs.com/docs/ai-naver-mapsdirections-driving
- NAVER Geocoding: https://api.ncloud-docs.com/docs/ai-naver-mapsgeocoding-geocode
- NAVER API HUB 지역 검색: https://api.ncloud-docs.com/docs/naver-api-hub-search-local

## License

GPL-2.0-or-later.
