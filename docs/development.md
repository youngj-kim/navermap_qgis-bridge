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
python -B tools/build_plugin.py --release --qgis4-launcher 'C:/Program Files/QGIS 4.2.2/bin/python-qgis.bat'
```

버전은 `metadata.txt`에서 읽으며 `--experimental`은 label 없는 시험 배포 파일명을 사용합니다. 정식 배포에는 `experimental=False`와 `--release`를 사용합니다. 현재 결과는 `dist/navermap_qgis_bridge-1.0.zip`입니다. 같은 파일을 덮어쓰지 않습니다. 다른 출력 폴더는 `--output-dir`로 지정합니다. `--label YOUR_TEST_LABEL`은 개발용 패키지이며 보안/Qt6 배포 검사를 수행하지 않으므로 업로드하지 않습니다.

생성기는 단일 플러그인 루트, Python 문법·내부 import·웹 리소스·ZIP CRC를 검사합니다. 한글·영문 설치 README, 사용·설치·문제 해결 가이드, 변경 기록과 수동 체크리스트를 포함하며 개발 테스트·빌드 도구·로컬 설정·캐시는 제외합니다. 설치용 README의 문서 링크는 ZIP 안에서 열려야 합니다.

## 변경과 배포 원칙

QGIS 3.34 이상과 4.x, 외부 브라우저와 내장 뷰어를 함께 고려합니다. 실제 실행하지 못한 항목을 통과로 표시하지 않습니다. API 키·`settings.json`·생성된 인증 포함 HTML을 커밋하지 않습니다. 라이선스는 GPL-2.0-or-later로 유지합니다.

릴리스 전에는 [배포 체크리스트](release-checklist.md)를 따르고, 변경 내용은 [CHANGELOG.md](../CHANGELOG.md), 상세 실행 결과는 [TESTING.md](../TESTING.md)에 기록합니다. 과거 설계 근거는 [리팩토링 기록](../REFACTORING.md)과 [기록 안내](archive/README.md)에 남깁니다.

## 저장소 보안 검사 재현

`--experimental`과 `--release`는 임시 ZIP을 풀어 실제 배포 내용에 Bandit·detect-secrets·Flake8 및 공식 QGIS Qt6 검사를 반드시 실행합니다. 누락된 도구, 시간 초과, 검사 오류, 탐지 결과 또는 Qt6 수정 권고가 있으면 최종 ZIP을 생성하지 않습니다. Qt6 검사는 QGIS 4 / Qt6 및 전체 QGIS 클래스가 필요하며 부분 검사로 대체하지 않습니다. 이 도구는 개발용이며 플러그인 실행 의존성에 추가하지 않습니다.

```powershell
python -m pip install --target dist/security-tools -r tools/security-requirements.txt
Invoke-WebRequest 'https://raw.githubusercontent.com/qgis/QGIS/master/scripts/pyqt5_to_pyqt6/pyqt5_to_pyqt6.py' -OutFile dist/pyqt5_to_pyqt6.py
python -B tools/build_plugin.py --release --qgis4-launcher 'C:/Program Files/QGIS 4.2.2/bin/python-qgis.bat'
```

QGIS 경로는 설치 환경에 맞게 지정하거나 `QGIS4_PYTHON` 환경변수로 설정합니다. `--scanner-path`와 `--qt6-checker`로 도구 위치를 바꿀 수 있습니다. 공식 검사기 SHA256은 `tools/release_checks.py`에 고정하며, 다운로드한 최신 파일이 달라지면 내용을 검토한 후 갱신해야 합니다. 자동 다운로드나 검사 생략 옵션은 없습니다.

통과한 ZIP 옆의 `.checks` 폴더에 검사 보고서, 도구 버전, Qt6 검사기 SHA256과 ZIP SHA256을 기록합니다. 검사 중 추출 파일이 바뀌어도 배포를 중단합니다. 이 과정은 정적 검사이며 QGIS 3.34/4의 동작 확인 및 수동 릴리스 체크리스트를 대신하지 않습니다.

0.99.1은 저장소가 보고한 Bandit 3건·비밀정보 탐지 7건 및 Qt6 4건을 대조해 수정했습니다. 설정 이름은 실제 키가 아니며 Python 상수명만 정리하고 실제 저장 키/환경변수는 유지합니다. GPX는 XML을 파싱하지 않고 생성만 하므로 해당 import의 B405 한 줄에 검토 근거를 남겼습니다. 회귀 검사는 XML 생성 API만 사용하도록 제한합니다. 전체 규칙·경로 제외나 baseline은 추가하지 않습니다.

로컬 결과는 서버 승인 보장이 아닙니다. [공식 보안 검사 안내](https://plugins.qgis.org/docs/security-scanning/tools)와 실제 새 버전의 Security/Qt6 결과를 함께 확인합니다.
