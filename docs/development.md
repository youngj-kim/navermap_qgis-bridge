# 개발·테스트·패키징

한국어 | [English](development.en.md)

[처음으로](../README.md) · [배포 체크리스트](release-checklist.md) · [검증 기록](../TESTING.md)

## 소스 구조

| 위치 | 역할 |
| --- | --- |
| `navermap_qgis_bridge/plugin.py` | 플러그인 수명, 설정 메뉴, 내장/외부 연결 |
| `api_protocol.py`, `api_requests.py`, `api_transport.py` | 순수 파라미터·Qt 요청·요청 수명 |
| `search_routes.py`, `route_inputs.py` | 검색·경로 조정과 입력 검증 |
| `route_history.py`, `history_operations.py`, `history_schema.py` | 이력·트랜잭션·필드 호환 |
| `history_exports.py`, `gpx_export.py` | GIS·GPX 파일과 스타일 |
| `canvas_sync.py`, `view_scale.py`, `map_layers.py` | 위치·축척 연동과 레이어 |
| `web_bridge.py`, `external_bridge.py`, `viewer_messages.py` | Qt/HTTP 계약과 응답 전달 |
| `viewer_document.py`, `web/viewer_assets.json` | 내장·외부 공통 웹 문서 조립 |
| `web/js/i18n.js`, `map_language.js`, `guidance_language.js` | UI 사전·언어 전환·기존 TBT 표시 변환 |
| `compat.py` | QGIS 3/4 API 차이 격리 |

표의 파일명만 표시한 항목도 `navermap_qgis_bridge/` 아래에 있습니다. 웹 manifest의 스크립트 순서는 초기화 순서이므로 임의로 바꾸지 않습니다. 원본 HTML에는 조립용 placeholder가 있어 파일을 직접 열어 실행하지 않습니다.

## 자동 검사

저장소 루트에서 실행합니다. 실제 인증키를 사용하지 않으며 필요한 개발 도구를 자동 설치하지 않습니다.

```powershell
python -B tests/run_checks.py --group core --group web
```

`core`에는 Python 입력·파라미터·전송·스키마·조립 검사가 포함됩니다. `web`은 Node.js와 테스트용 Playwright를 사용해 모의 SDK로 언어·검색·외부 명령·축척·화면·이력을 확인합니다. 환경에 따라 `--node` 또는 `NODE_PATH`가 필요합니다. 설치된 Chrome을 쓰려면 `TEST_BROWSER_CHANNEL=chrome`을 설정합니다.

웹 개발 의존성은 `tests/web/package.json`에 정의합니다. 필요한 경우에만 설치합니다.

```powershell
npm --prefix tests/web install
npm --prefix tests/web exec -- playwright install chromium
```

QGIS 런타임 검사는 설치된 실행기를 지정합니다. 다음 경로는 개발 환경 예시이며 PC의 실제 설치 경로로 바꿉니다.

```powershell
python -B tests/run_checks.py --group qgis --qgis-launcher 'C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat' --qgis-launcher 'C:\Program Files\QGIS 4.2.2\bin\python-qgis.bat'
```

이 검사는 레이어·파일·localhost HTTP·프로젝트 수명·이력 정밀도·일괄 작업·요청 언어를 확인합니다. 기본 8083 포트 검사는 실행 중인 서비스와 충돌할 수 있으므로 다른 QGIS 외부 연동을 종료하고 수행합니다. 실제 NAVER SDK 화면 검증은 [설치 체크리스트](install-test-checklist.md)로 별도 기록합니다.

## 설치 ZIP 생성

```powershell
python -B tools/build_plugin.py --label test-20261027-docs
```

버전은 `metadata.txt`에서 읽고 label은 파일명에만 붙입니다. 결과는 `dist/navermap_qgis_bridge-0.2.0-test-20261027-docs.zip`입니다. 같은 파일을 덮어쓰지 않으므로 재빌드 시 label을 바꿉니다.

생성기는 단일 플러그인 루트, Python 문법·내부 import·웹 리소스·ZIP CRC를 검사합니다. 한글·영문 설치 README, 사용·설치·문제 해결 가이드, 변경 기록과 수동 체크리스트를 포함하며 개발 테스트·빌드 도구·로컬 설정·캐시는 제외합니다. 설치용 README의 문서 링크는 ZIP 안에서 열려야 합니다.

## 변경과 배포 원칙

QGIS 3.34 이상과 4.x, 외부 브라우저와 내장 뷰어를 함께 고려합니다. 실제 실행하지 못한 항목을 통과로 표시하지 않습니다. API 키·`settings.json`·생성된 인증 포함 HTML을 커밋하지 않습니다. 라이선스는 GPL-2.0-or-later로 유지합니다.

릴리스 전에는 [배포 체크리스트](release-checklist.md)를 따르고, 변경 내용은 [CHANGELOG.md](../CHANGELOG.md), 상세 실행 결과는 [TESTING.md](../TESTING.md)에 기록합니다. 과거 설계 근거는 [리팩토링 기록](../REFACTORING.md)과 [기록 안내](archive/README.md)에 남깁니다.
