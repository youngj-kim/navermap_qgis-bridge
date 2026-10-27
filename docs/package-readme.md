# Naver Map QGIS Bridge 0.2.0

한국어 | [English](README.en.md)

QGIS와 NAVER 지도·로드뷰를 연동하고 장소 검색, 자동차 경로·안내, 이력 저장과 GIS 파일 내보내기를 지원합니다. QGIS 3.34 LTR 이상 및 4.x를 대상으로 하는 실험적 개발본입니다.

## 시작하기

1. QGIS의 **플러그인 관리 및 설치 → ZIP에서 설치**로 이 패키지를 설치합니다.
2. QGIS를 다시 시작하고 **Naver Map QGIS Bridge**를 활성화합니다.
3. Maps Application에서 Dynamic Map·Geocoding·Directions 5와 Web URL `http://localhost` 등록을 확인합니다.
4. 플러그인 메뉴에서 Maps Client ID / Client Secret을 설정하고 **Naver Map / Street View**를 엽니다.
5. 장소명 검색에는 별도의 NAVER API HUB Client ID / Client Secret을 설정합니다.

키는 QGIS 사용자 설정에 저장되며 별도로 암호화하지 않습니다. 환경변수가 저장 설정보다 우선합니다. 실제 키를 다른 사람에게 보내거나 이 폴더에 저장하지 마세요.

## 동봉 문서

- [설치·업데이트·API 키 설정](docs/setup.md)
- [사용 가이드](docs/usage.md)
- [문제 해결](docs/troubleshooting.md)
- [릴리즈 노트와 변경 기록](CHANGELOG.md)
- [설치 후 체크리스트](docs/install-test-checklist.md) · [브라우저 체크리스트](docs/install-test-checklist.html)

기본 검색은 한글입니다. EN에서 새 경로 생성 시 영문 지명 안내를 요청합니다. 기존 이력은 저장 당시의 원문을 유지하므로 언어 전환만으로 지명이나 경로를 다시 조회하지 않습니다.

탐색창을 처음 접어도 이력은 표시되며 안내·이력은 −/+로 따로 접고 펼칩니다. 외부 브라우저는 도크의 **외부 연동 창 열기**로 새 탭을 여세요. QGIS를 켜 둔 상태에서 사용하고 이전 세션 탭은 닫습니다.

종료 전에 필요한 이력을 GeoPackage로 저장하세요. 체크박스 일괄 삭제는 세션 이력에만 적용되며 원본 파일은 삭제하지 않습니다. SHP 문자열 한도 초과 시에는 GPKG/GeoJSON을 사용합니다.

2026-10-27 사용자가 fix4 수정본의 정상 작동을 확인했습니다. 개발 검증 환경은 Windows QGIS 3.44.14 / 4.2.2이며 정확한 QGIS 3.34와 모든 운영체제·뷰어 조합의 전체 검증을 뜻하지 않습니다. 메타데이터 버전은 0.2.0이며 GitHub Release는 아직 게시하지 않았습니다.

개발 문서·검증 기록·소스는 [GitHub 저장소](https://github.com/youngj-kim/navermap_qgis-bridge)를 참고하세요. 이 설치 패키지에는 개발 테스트와 빌드 도구를 포함하지 않습니다.

## 라이선스

[GPL-2.0-or-later](LICENSE). NAVER API에는 제공처의 이용 조건과 사용량 제한이 적용됩니다. 이 플러그인은 NAVER의 공식 제품이 아니며 지도 타일을 QGIS XYZ/TMS 레이어로 등록하지 않습니다.
