# Naver Map QGIS Bridge

한국어 | [English](README.en.md)

QGIS와 NAVER 지도·로드뷰의 위치와 확대 수준을 연동합니다. 장소·주소 검색, 자동차 경로와 순서별 안내, 경로 이력 저장 및 GIS 파일 내보내기를 지원합니다.

**현재 버전: 0.99.1 · 실험적 시험 배포** · [사용 가이드](docs/usage.md) · [설치와 API 키 설정](docs/setup.md) · [변경 기록](CHANGELOG.md)

## 설치와 시작

1. 플러그인 설치용 ZIP을 QGIS의 **플러그인 관리 및 설치 → ZIP에서 설치**로 설치합니다.
2. QGIS를 다시 시작하고 **Naver Map QGIS Bridge**를 활성화합니다.
3. NAVER Cloud의 Maps Application에서 Dynamic Map·Geocoding·Directions 5 사용 설정과 Web URL `http://localhost` 등록을 확인합니다.
4. 플러그인 메뉴에서 Maps Client ID / Client Secret을 설정하고 **Naver Map / Street View**를 엽니다.
5. 업체·기관명 검색을 사용하려면 별도의 NAVER API HUB Client ID / Client Secret도 설정합니다.

각 사용자는 자신의 인증 정보를 사용합니다. 발급 위치, 네 가지 키의 구분, 외부 브라우저 실행과 업데이트는 [설치와 API 키 설정](docs/setup.md)을 참고하세요.

0.99.1 시험 배포 ZIP을 QGIS 플러그인 저장소 업데이트용으로 준비했습니다. 문제 확인·보완 후 1.0 정식 배포를 계획합니다. 저장소 업로드·승인과 GitHub Release 게시는 별도 단계입니다. 저장소의 **Code → Download ZIP**은 소스 묶음이며 QGIS 설치용 ZIP과 다릅니다. 설치용 ZIP을 받았거나 소스에서 패키지를 만들 때의 절차를 설치 문서에 정리했습니다.

## 주요 기능

- QGIS↔NAVER 지도 이동·확대·축소 연동과 로드뷰 위치·방향 표시
- 장소·주소·경도/위도 검색, 일반·위성 지도와 로드뷰 촬영 도로 표시
- 자동차 경로, 최대 5개 경유지, 회피·차량 설정과 순서별 안내
- 안내·이력을 독립적으로 접고 펼치기, 상하·좌우 네 가지 배치와 전체화면
- 이력 파일 여러 개 불러오기, 체크박스 선택·일괄 삭제
- GeoPackage·GeoJSON·Shapefile·GPX 내보내기
- **EN / KR** 전환과 EN에서 새 경로 생성 시 API가 제공하는 영문 지명 안내

## 지원 환경과 확인 범위

| 구분 | 지원 대상과 동작 |
| --- | --- |
| QGIS | 3.34 LTR 이상 및 QGIS 4.x |
| 내장 뷰어 | Qt WebEngine과 WebChannel을 사용할 수 있는 환경 |
| 외부 브라우저 | 내장 웹 뷰를 사용할 수 없는 환경의 대체 모드. QGIS 3에서도 사용 |
| 개발 검증 | Windows QGIS 3.44.14 / 4.2.2 런타임 및 모의 SDK 웹 검사 |

2026-10-27 사용자가 `fix4` 수정본의 정상 작동을 확인했습니다. 정확한 QGIS 3.34와 모든 운영체제·뷰어 조합의 확인을 의미하지는 않습니다. 상세 검증 결과는 [TESTING.md](TESTING.md)에 보존합니다.

## 사용 시 알아둘 점

경로 이력은 세션에서 관리합니다. 종료 전에 **GeoPackage로 저장**하세요. 프로젝트 전환과 플러그인 종료의 이력 수명은 다릅니다. 파일 보존 방법은 [사용 가이드](docs/usage.md)에 설명합니다.

기본 언어와 장소 검색은 한글입니다. EN에서 새 경로를 생성하면 영문 안내를 요청하며, 기존 이력은 저장 당시의 원문을 유지합니다. 언어 전환만으로 경로를 다시 조회하지 않습니다.

지도는 NAVER SDK로 표시하며 QGIS XYZ/TMS 배경지도로 등록하지 않습니다. **현재 위치**는 GPS가 아닌 NAVER 지도 중심입니다. API 키는 QGIS 사용자 설정에 저장되며 플러그인에서 별도로 암호화하지 않습니다.

## 문서

| 필요한 내용 | 문서 |
| --- | --- |
| 설치·업데이트·API 키·localhost | [설치와 API 키 설정](docs/setup.md) |
| 화면 조작·검색·경로·이력·언어 | [사용 가이드](docs/usage.md) |
| 인증 오류·연결·저장 문제 | [문제 해결](docs/troubleshooting.md) |
| 버전별 변경과 개발 이력 | [릴리즈 노트와 변경 기록](CHANGELOG.md) |
| 설치 후 확인 | [수동 체크리스트](docs/install-test-checklist.md) · [브라우저 체크리스트](docs/install-test-checklist.html) |
| 개발·테스트·패키징 | [개발 안내](docs/development.md) · [배포 체크리스트](docs/release-checklist.md) |
| 카카오와 요금 비교 | [GPKG 요금 비교](docs/fare-comparison.md) |
| 과거 구현·검토·검증 | [기록 안내](docs/archive/README.md) |

## 라이선스

[GPL-2.0-or-later](LICENSE). NAVER 지도와 API에는 제공처의 이용 조건과 사용량 제한이 적용됩니다. 이 프로젝트는 NAVER의 공식 제품이 아니며 실제 API 키와 지도 타일을 배포하지 않습니다.
