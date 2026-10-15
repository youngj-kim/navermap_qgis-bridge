# 리팩토링 기반 (2026-10-08)

## 2026-10-15 코드 검토 수정 정리

- `credential_validation.py`: 설정 저장과 HTTP 요청 경계에서 공통 ASCII 인증키 검증.
- `history_operations.py`: 이력 피처 추가 결과 확인, 실패 복구, 가져오기 쌍의 좌표계·지오메트리·속성·안내 일관성 검증.
- 안내 분류는 NAVER Directions 코드표를 사용한다. 가져오기·표시·내보내기 및 같은 GPKG 재저장에서 오래된 분류를 보정한다.
- 외부 HTTP 서버는 세션 토큰, Host/Origin, JSON Content-Type을 검사한다. Windows 독점 소켓과 충돌 시 대체 포트를 사용하고, 이벤트 재진입·누락·새 탭의 오래된 입력 재생을 제어한다.
- SHP의 UTF-8 바이트 폭 초과는 오류로 처리하고 GPX의 XML 금지 문자를 제거한다. 선택 이력 내보내기도 실제 파생 파일의 덮어쓰기를 확인한다.
- 설치 ZIP은 사용자용 README와 설치 체크리스트를 포함한다. 개발 문서·테스트·빌드 도구는 소스에서 관리한다.
- 2026-10-15 사용자 확인은 이상 없음이며 환경별 상세 검증 범위는 [TESTING.md](TESTING.md)에 구분한다. Mixin 구조 개편과 내장 JS fallback 중복 전달 제거는 후속 작업이다.

## 2026-10-13 후속 분리

- `route_inputs.py`: QGIS·인증·네트워크·UI에 의존하지 않는 경로 입력 검증. 호스트는 검증 결과를 받아 요청과 표시를 조정합니다.
- `history_schema.py`: 메모리 이력 필드 순서/타입, SHP 단축명·길이와 가져오기 매핑의 공통 기준. 기존 파일 스키마와 GPX 확장은 유지합니다.
- `view_scale.py`: 좌표계 단위와 분리된 지상 거리 계산. 캔버스와 웹에서 화면 128픽셀의 지상 거리를 기준으로 축척을 맞춥니다.
- `web/js/viewer_options.js`: 지도 접근·SDK·레이아웃·오류 콜백을 인자로 받는 표시 설정 모듈. 경로·이력·위치 이동을 직접 변경하지 않습니다.
- 플러그인이 프로젝트 세대와 세션 이력 수명을 소유하고, 현재 표시 레이어는 프로젝트 전환 때 참조를 초기화합니다. HTTP 입력·응답에는 세대를 포함하며 이전 세대 이벤트를 차단합니다.
- 경로 취소/30초 제한은 `ApiTransport`에서 소유권 해제 후 처리합니다. 웹의 위치 해석은 별도 세대 번호로 늦은 Promise 결과를 차단합니다.

전체 Mixin을 독립 controller로 바꾸거나 이력 파일 버전을 올리는 작업은 이번 단계에 포함하지 않았습니다. [구현 기록](docs/implementation-progress.md)에 남은 확장 항목과 실제 연동 검증을 구분합니다.

기능 확장 없이 기존 동작의 책임 경계를 정리했습니다. 실제 NAVER/QGIS 화면 검증과 릴리스는 별도 단계입니다.

## Python 책임 경계

| 모듈 | 책임 |
| --- | --- |
| `plugin.py` | 플러그인 초기화/종료, 설정 입력, Dock 및 외부 서버 연결 |
| `search_routes.py` | 검색·경로 요청 조정, 응답을 QGIS 작업으로 연결 |
| `api_transport.py` | 요청 등록, 완료/검색 시간 제한 연결, 취소/종료 |
| `api_requests.py` | Qt HTTP 요청 생성과 응답 읽기 |
| `api_protocol.py` | 엔드포인트, 요청 파라미터, JSON 및 오류 응답 해석 |
| `route_history.py` | 이력 레이어, 목록, 선택, 불러오기, 삭제 |
| `history_exports.py` | GPKG/GeoJSON/SHP/GPX 파일 및 스타일 입출력 |
| `gpx_export.py`, `data_transforms.py` | QGIS 없는 XML/데이터 변환 |
| `map_layers.py` | 경로/안내/출발·도착/로드뷰 메모리 레이어와 심볼 |
| `canvas_sync.py` | 좌표계 변환, 지도 중심 동기화와 루프 방지 |
| `viewer_messages.py` | 내장/외부 뷰어 응답 전달 |
| `web_bridge.py`, `external_bridge.py` | Qt 신호/슬롯 계약, 로컬 HTTP 서버 |
| `viewer_document.py` | 두 모드 공통 웹 문서 조립 |
| `constants.py`, `compat.py`, `settings.py` | 공통 상수, 버전 호환, 로컬 설정 |

### 공유 상태 계약

역할별 `*Mixin`은 새로운 플러그인이나 독립 QObject가 아닙니다. `NaverMapQgisBridgePlugin`의 일부이며 `iface`, Dock, 레이어 참조, 요청 상태와 기존 `self._...` 호출을 공유합니다. 상태 초기화/수명은 플러그인에서 한 번만 관리합니다. 중복 생성자와 순환 import를 만들지 않습니다.

이 단계는 상태 소유권과 동작을 동시에 변경하지 않기 위한 기반 분리입니다. 각 mixin을 단독으로 인스턴스화하지 않습니다. 향후 독립 controller로 전환하려면 공유 상태와 호출 계약을 먼저 명시적으로 전달하고 회귀 검증해야 합니다.

`ApiTransport`와 `ViewerMessages`는 주입된 객체/콜백으로 동작하며 QGIS 없이 테스트할 수 있습니다. 검색은 기존 7초 제한을 유지합니다. 경로 요청에 새로운 시간 제한이나 재시도 정책은 추가하지 않았습니다. 종료/취소 시 소유권을 먼저 해제하여 늦은 콜백이 폐기된 요청을 처리하지 않게 합니다.

## 웹 소스와 배포

- `web/navermap_viewer.html`: HTML 구조와 조립 placeholder.
- `web/viewer.css`: 레이아웃/색상/표시 규칙.
- `web/js/`: 상태, 분할 레이아웃, 유틸리티, 이력 UI, 브리지, 경로 입력, 동기화, 검색, SDK 이벤트, 위치 이동.
- `web/viewer_assets.json`: JavaScript 조립 순서의 단일 기준. 기존 전역 lexical scope와 초기화 순서를 유지하므로 순서를 임의로 바꾸지 않습니다.
- `web/js/external_transport.js`: 외부 브라우저 전용 HTTP 어댑터. 공통 manifest에 넣지 않고 외부 문서에만 주입합니다.

QGIS `setHtml`과 외부 HTTP 서버는 모두 `build_viewer_html()`을 사용합니다. CSS/JS는 최종 문서에 인라인으로 조립하므로 정적 파일 서버나 상대 URL 로딩이 필요하지 않습니다. 원본 HTML을 직접 브라우저에서 열어서는 완성된 뷰어가 나오지 않습니다. 패키지에는 HTML뿐 아니라 CSS·manifest·모든 JS·SVG를 포함해야 합니다.

진단 빌드/역방향 동기화 표시를 보려면 QGIS 시작 전 `NAVER_BRIDGE_DEBUG=1`을 설정합니다. 기본 모드에서는 두 표시를 숨기지만 연결 오류 메시지와 진단 동작 자체는 유지합니다. API 키는 조립 시에만 전달하며 소스/테스트/생성 문서를 커밋하지 않습니다.

## 검증과 남은 범위

실행 명령과 결과는 `TESTING.md`를 기준으로 합니다. 기본 검증은 Python 단위 테스트, 조립 일치, 전역 의존성/메서드 연결, JS 문법, 모의 SDK/HTTP 계약 테스트입니다. `tests/qgis_smoke.py`는 실제 QGIS에서 합성 데이터로 로딩·레이어·파일 입출력을 검증하며 사용자 프로젝트나 NAVER 인증을 사용하지 않습니다.

실제 외부 브라우저/내장 WebEngine, NAVER POI/주소 검색, 인증 실패, 경로 취소, 지도/로드뷰 이동, 촬영일 및 화면 크기 변경의 최종 수동 매트릭스는 아직 남아 있습니다. 정확한 QGIS 3.34 런타임 검증도 별도로 필요합니다. 설치 폴더만 남아 있는 3.34 환경을 실행 가능한 것으로 간주하지 않습니다.

카카오 플러그인의 추가 기능 이식, 새 기능, API 정책 변경, 릴리스 버전 변경, 커밋/푸시는 이번 리팩토링에 포함하지 않았습니다.

## 라이선스

프로젝트 소스는 GPL-2.0-or-later입니다. Playwright는 테스트 전용 외부 개발 의존성(Apache-2.0, 출처: https://github.com/microsoft/playwright)이며 플러그인 ZIP에는 라이브러리나 브라우저 바이너리를 포함하지 않습니다.
