# 요금 저장과 카카오 GPKG 비교 연동 — 개발 후보

새 NAVER 경로 응답의 `summary.tollFare`와 `summary.taxiFare`를 원 단위 정수로 저장한다.
공통 이력 필드명은 `toll_fare`, `taxi_fare`다. GPKG·GeoJSON·SHP 내보내기와 이력
가져오기에서 필드를 보존한다. 기존 파일의 누락 요금은 NULL로 유지하며 0원으로 추정하지 않는다.
기존 경로에 요금을 소급 복원하지 않으므로 새 조회 후 별도 파일로 내보낸다.
GPX 출력은 기존 확장 스키마를 유지하며 이번 NAVER 요금 비교의 입력 형식이 아니다.

카카오 비교창에서 통행료와 예상 택시요금을 각각 A/B 금액 및 차액(B−A)으로 표시한다.
어느 쪽이든 요금이 없으면 해당 차액은 비교 불가다. 예상 택시요금과 통행료를 합산하지 않는다.
서비스별 조회 시점·차량·할증 계산이 다르므로 실제 청구액이나 같은 계산 조건을 보장하지 않는다.

API 필드 출처: https://api.ncloud-docs.com/docs/application-maps-directions5
두 프로젝트 연동 검사는 카카오 프로젝트의 `tests/qgis_fare_comparison_smoke.py`에
이 프로젝트 경로를 첫 인수로 전달한다. 합성 API 응답을 사용하며 인증·유료 요청은 하지 않는다.
QGIS 3.44.14/4.2.2에서 API 응답 → 메모리 이력 → GPKG/GeoJSON/SHP → 비교 UI를 검증했다.
정확한 QGIS 3.34 및 실제 API/지도 화면 검증은 아직 하지 않았다.

패키지는 기존 0.2.0 메타데이터를 유지한 `navermap_qgis_bridge-fares-test.zip`으로
제공한다. 기존 미커밋 변경을 포함하는 작업 트리의 테스트 패키지이며 공식 배포용이 아니다.
