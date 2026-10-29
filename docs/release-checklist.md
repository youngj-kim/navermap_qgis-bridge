# 배포 체크리스트

한국어 | [English](release-checklist.en.md)

[처음으로](../README.md) · [변경 기록](../CHANGELOG.md) · [개발 안내](development.md)

현재 `1.0`은 정식 배포 준비 버전이며, 실험적 버전 `0.99.1`은 사용자 확인으로 저장소 승인이 완료됐습니다. 아래 항목은 다음 배포를 준비하기 위한 기준이며 완료 결과를 뜻하지 않습니다. 문서 정리나 테스트 ZIP 생성만으로 버전·태그·GitHub Release를 올리지 않습니다.

## 버전과 문서

- [ ] `navermap_qgis_bridge/metadata.txt`의 버전을 배포 기준으로 확정한다.
- [ ] CHANGELOG에 변경·업데이트 방법·확인 범위와 남은 제한을 기록한다.
- [ ] README, 설치·사용·문제 해결 문서, 설치용 README의 한글·영문판이 같은 동작을 설명하는지 확인한다.
- [ ] 설치 ZIP 이름의 label과 정식 버전을 혼동하지 않도록 한다.

## 환경별 검증

- [ ] Python core와 모의 SDK 웹 검사를 실행하고 결과를 기록한다.
- [ ] QGIS 3.34 LTR 이상에서 외부 브라우저를 포함한 관련 시나리오를 확인한다.
- [ ] QGIS 4.x에서 내장 웹 뷰와 좌표·경로·이력 기능을 확인한다.
- [ ] 인증·검색·경로·이력·언어·공통 레이아웃 변경을 양쪽 환경에서 확인한다.
- [ ] [설치 체크리스트](install-test-checklist.md)에 환경과 실제 결과를 기록한다. 미수행은 통과와 구분한다.

## 보안과 패키지

- [ ] `git diff`와 `git status`에 실제 키·`settings.json`·개인 파일이 없는지 확인한다.
- [ ] 소스와 포함 리소스가 GPL-2.0-or-later와 호환되는지, 외부 출처·라이선스가 기록됐는지 확인한다.
- [ ] 빌드 도구로 ZIP을 만들고 최상위가 `navermap_qgis_bridge/` 하나인지 확인한다.
- [ ] `--experimental` 또는 `--release` 빌드의 보안·Qt6 필수 검사를 통과하고, `.checks/summary.json`의 SHA256이 제출 ZIP과 일치하는지 확인한다. 도구 설치와 실행은 [개발 안내](development.md)를 따른다.
- [ ] Python 모듈·manifest의 모든 웹 리소스·LICENSE·사용자 문서가 포함됐는지 확인한다.
- [ ] 키·로컬 설정·캐시·개발 의존성·사용자 이력 데이터가 ZIP에 없는지 확인한다.
- [ ] ZIP 안 README의 상대 문서 링크와 CRC를 확인하고 SHA256을 기록한다.
- [ ] 별도 QGIS 프로필에서 ZIP 신규 설치·업데이트·재시작을 확인한다.

## 게시

검증한 버전·커밋·ZIP·릴리즈 노트가 일치하는지 확인한 뒤 승인된 배포를 진행합니다. GitHub Release를 게시할 때는 소스 자동 압축본과 별도로 QGIS 설치용 ZIP을 첨부합니다. 게시 후 다운로드한 ZIP으로 구조·해시·문서 링크를 재확인합니다.

## QGIS 저장소에 1.0 정식 버전 제출하기

1. 업로드 권한이 있는 계정으로 [QGIS 플러그인 저장소](https://plugins.qgis.org/)에 로그인합니다.
2. 기존 플러그인의 소유권과 버전 목록을 확인합니다. 이미 `1.0`가 등록돼 있으면 같은 버전으로 덮어쓸 수 없으므로 다음 버전을 정해야 합니다.
3. [Upload a plugin](https://plugins.qgis.org/plugins/add/)에서 `navermap_qgis_bridge-1.0.zip`을 선택합니다. 기존 모듈명 `navermap_qgis_bridge`와 플러그인 이름은 유지합니다.
4. 읽어 온 버전 1.0, 최소 QGIS 3.34, 최대 4.99, Experimental 해제, 소스·홈페이지·이슈 링크와 영문 소개를 확인합니다.
5. 등록 결과를 확인하고 심사·승인 상태를 기록합니다. 제출만으로 공개·승인이 완료된 것은 아닙니다.

최소 문서, 영문 설명, 공개 소스·홈페이지·이슈 링크, GPL 호환 라이선스와 패키지 구조는 [QGIS 공식 게시 요건](https://plugins.qgis.org/docs/publish)을 기준으로 점검합니다. 제출 ZIP은 25MB 이하이며 실제 키·실행 바이너리를 포함하지 않아야 합니다. [배포 문서](https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/plugins/releasing.html)의 버전 고유성과 단일 플러그인 폴더 요건도 확인합니다.

계정 소유권·기존 등록 버전·심사 결과는 로그인한 저장소 화면에서 확인해야 합니다. 로컬 ZIP 검증을 저장소의 업로드·승인 완료로 기록하지 않습니다.
