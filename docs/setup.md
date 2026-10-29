# 설치와 API 키 설정

한국어 | [English](setup.en.md)

[처음으로](../README.md) · [사용 가이드](usage.md) · [문제 해결](troubleshooting.md)

## 1. 준비

QGIS 3.34 LTR 이상 또는 QGIS 4.x, 인터넷 연결, 본인의 NAVER Cloud 인증 정보를 준비합니다. Python·Node.js·Playwright를 따로 설치할 필요는 없습니다. 이 도구들은 소스 개발과 테스트에만 사용합니다.

내장 지도는 Qt WebEngine과 WebChannel이 필요합니다. 사용할 수 없으면 플러그인이 외부 브라우저 연동 화면을 제공합니다. QGIS 버전 번호만으로 내장 웹 뷰 사용 여부가 결정되지는 않습니다.

## 2. 설치와 업데이트

### 설치용 ZIP 사용

1. 전달받은 설치용 ZIP을 준비합니다. 압축 내부 최상위에는 `navermap_qgis_bridge` 폴더 하나가 있어야 합니다.
2. QGIS에서 **플러그인 → 플러그인 관리 및 설치 → ZIP에서 설치**를 엽니다. QGIS 언어에 따라 메뉴 표기는 다를 수 있습니다.
3. ZIP을 선택해 설치하고 QGIS를 다시 시작합니다.
4. 설치된 플러그인 목록에서 **Naver Map QGIS Bridge**를 활성화합니다.
5. **Naver Map / Street View** 메뉴 또는 툴바 버튼으로 엽니다.

업데이트 전에는 필요한 이력을 파일로 저장하고 기존 외부 브라우저 탭을 닫으세요. 새 ZIP으로 설치한 뒤 QGIS를 다시 시작하고 플러그인에서 새 탭을 엽니다. 같은 QGIS 프로필의 인증 설정은 플러그인 폴더와 별도로 저장됩니다.

현재 메타데이터 버전은 `1.0`이며 정식 버전입니다. `fix4`는 이전 0.2.0 테스트 패키지의 구분자입니다. 1.0 정식 배포에는 `navermap_qgis_bridge-1.0.zip`을 사용합니다. 설치 패키지는 [Releases](https://github.com/youngj-kim/navermap_qgis-bridge/releases)에서 확인할 수 있습니다.

### 소스 설치

저장소의 **Code → Download ZIP**을 QGIS 설치 창에 직접 넣지 마세요. 소스에는 개발 문서·테스트가 함께 있습니다. [개발 안내](https://github.com/youngj-kim/navermap_qgis-bridge/blob/main/docs/development.md)의 빌드 도구로 설치 ZIP을 만들거나 플러그인 폴더만 복사합니다.

실제 프로필 폴더는 QGIS의 **설정 → 사용자 프로필 → 활성 프로필 폴더 열기**에서 확인하고, 그 아래 `python/plugins/navermap_qgis_bridge`에 설치합니다. `web` 하위 HTML·CSS·JavaScript·manifest·SVG를 모두 포함해야 합니다. 개발 소스를 정션/심볼릭 링크로 연결했다면 ZIP 설치는 별도 프로필에서 테스트하세요.

## 3. 필요한 API와 키 구분

| 기능 | NAVER 서비스 | 플러그인에 입력할 값 |
| --- | --- | --- |
| 지도·로드뷰 | Maps의 Dynamic Map / JavaScript API | Maps Client ID |
| 주소 검색 | Maps의 Geocoding (JavaScript SDK) | Maps Client ID |
| 자동차 경로·영문 지명 안내 | Maps의 Directions 5 | Maps Client ID + Client Secret |
| 업체·기관·장소명 검색 | NAVER API HUB의 검색 → 지역 | API HUB Client ID + Client Secret |

Maps 인증 정보와 API HUB 인증 정보는 플러그인에서 별도로 관리합니다. NAVER Developers의 일반 검색 API 키나 Cloud 관리용 Access Key를 이 입력창에 대신 넣지 마세요. 지역 검색은 [NAVER API HUB 지역 검색](https://api.ncloud-docs.com/docs/naver-api-hub-search-local)의 엔드포인트와 인증 방식을 사용합니다.

### Maps Application

1. [NAVER Cloud 콘솔](https://console.ncloud.com/)에서 Maps 서비스를 찾아 Application을 생성하거나 기존 Application을 선택합니다.
2. Dynamic Map, Geocoding, Directions 5를 사용할 수 있도록 설정합니다.
3. 인증 정보에서 Client ID와 Client Secret을 확인합니다.
4. 서비스 환경의 **Web URL**에 아래 주소를 등록합니다.

```text
http://localhost
```

콘솔 Web URL에는 포트 번호와 경로를 넣지 않습니다. 이는 [NAVER 공식 인증 문제 해결 안내](https://guide.ncloud-docs.com/docs/application-maps-troubleshoot)에 따른 설정입니다. 콘솔 개편으로 메뉴 위치가 달라질 수 있으므로 해당 서비스의 Application·인증 정보 화면을 기준으로 확인하세요.

### NAVER API HUB

NAVER Cloud의 NAVER API HUB에서 **검색 → 지역**을 사용할 Application과 인증 정보를 확인합니다. Maps 키와 구분해 Client ID / Client Secret을 준비합니다. 서비스 이용 신청·사용량·요금 조건은 [NAVER API HUB 공식 문서](https://api.ncloud-docs.com/docs/naver-api-hub-overview)를 확인하세요.

## 4. QGIS에 인증 정보 입력

플러그인 메뉴의 다음 네 항목에 각각 입력합니다.

| 메뉴 | 입력 값 |
| --- | --- |
| Naver Maps Client ID 설정... | Maps Client ID |
| Naver Maps Client Secret 설정... | Maps Client Secret |
| Naver API HUB Client ID 설정... | API HUB Client ID |
| Naver API HUB Client Secret 설정... | API HUB Client Secret |

키는 공백·줄바꿈 없는 인쇄 가능한 ASCII 문자여야 합니다. 값은 현재 QGIS 사용자 프로필의 설정에 저장됩니다. 플러그인은 별도 암호화를 제공하지 않으므로 프로필과 PC 접근 권한을 관리하세요. 키를 오류 보고·스크린샷·저장소에 포함하지 않습니다.

### 환경변수 사용

환경변수가 QGIS에 저장한 값보다 우선합니다. 다음 PowerShell 예시의 ID는 placeholder이며 Client Secret은 실행 시 입력합니다. Read-Host 입력은 화면에 보이므로 공유 화면에서는 QGIS의 비밀 입력창을 사용하세요. 이 환경을 상속하는 프로세스에서 QGIS를 실행해야 합니다. 이미 실행 중인 QGIS에는 나중에 설정한 값이 반영되지 않습니다.

```powershell
$env:NAVER_MAP_CLIENT_ID = "YOUR_NAVER_MAP_CLIENT_ID"
$env:NAVER_MAP_CLIENT_SECRET = Read-Host "Maps Client Secret 입력"
$env:NAVER_API_HUB_CLIENT_ID = "YOUR_NAVER_API_HUB_CLIENT_ID"
$env:NAVER_API_HUB_CLIENT_SECRET = Read-Host "API HUB Client Secret 입력"
```

예전 `settings.json`은 Maps JavaScript Client ID의 이전 호환 경로로만 읽습니다. 새 설치는 QGIS 설정 또는 환경변수를 사용하세요. 예시 JSON을 복사하는 것만으로 네 종류의 인증 정보가 모두 설정되지는 않습니다.

## 5. localhost와 외부 브라우저

| 구분 | 주소·역할 |
| --- | --- |
| NAVER 콘솔 등록 | `http://localhost` — 포트·경로 제외 |
| 내장 뷰어 기본 출처 | `http://localhost:8083/navermap_qgis_bridge/` |
| 외부 연동 | 기본 포트 8083의 로컬 서버. 사용 중이면 별도 포트로 시작 |

외부 모드에서는 QGIS 도크의 **외부 연동 창 열기** 버튼을 누릅니다. QGIS를 켜 둔 상태에서 사용하며, 플러그인이 연 새 주소를 사용해야 세션 인증과 명령 전달이 됩니다. 이전 세션의 탭·주소를 재사용하지 마세요.

`NAVER_MAP_BASE_URL`은 내장 문서의 출처를 직접 지정할 때 사용하는 고급 설정입니다. 보통 설정할 필요가 없습니다. 이전에 8082 등 다른 값으로 지정했다면 환경변수를 해제해 기본값을 쓰거나 아래 값으로 수정하고 QGIS를 재시작합니다. 외부 서버의 실제 포트를 고정하는 설정은 아닙니다.

```powershell
$env:NAVER_MAP_BASE_URL = "http://localhost:8083/navermap_qgis_bridge/"
```

## 6. 첫 실행 확인

지도·로드뷰 표시 → `127.1,37.4` 좌표 이동 → 장소·주소 검색 → 짧은 경로 생성 → GeoPackage 저장 순서로 확인합니다. EN의 영문 지명은 **EN을 선택한 뒤 새 경로를 생성**해서 확인하세요. 문제가 있으면 [증상별 해결 방법](troubleshooting.md)을 참고합니다.
