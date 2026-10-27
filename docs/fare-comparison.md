# NAVER 이력과 카카오 GPKG 요금 비교

한국어 | [English](fare-comparison.en.md)

[처음으로](../README.md) · [이력 저장과 내보내기](usage.md)

## 비교 순서

1. NAVER에서 비교할 자동차 경로를 새로 생성합니다.
2. **경로 이력 GeoPackage 저장...** 또는 개별 이력 내보내기로 GPKG를 저장합니다.
3. 비교 기능이 있는 [Kakao QGIS Bridge](https://github.com/youngj-kim/kakao_qgis-bridge)를 열고 **GPKG 경로 비교**에서 NAVER 파일을 선택합니다.
4. 비교할 경로를 선택해 거리·시간·통행료·예상 택시요금을 확인합니다.

비교 화면은 카카오 플러그인의 기능입니다. NAVER 플러그인이 별도의 비교창을 제공하는 것은 아닙니다. 비교 형식은 GPKG를 사용하며, GPX는 이 비교의 입력 형식이 아닙니다.

## 저장 값과 해석

| 값 | NAVER 응답 | 이력 필드 |
| --- | --- | --- |
| 통행료 | `summary.tollFare` | `toll_fare` |
| 예상 택시요금 | `summary.taxiFare` | `taxi_fare` |

금액은 원 단위 정수로 보존합니다. 두 필드는 GPKG·GeoJSON·SHP 저장과 가져오기에서 유지되며, 요금이 없는 기존 파일의 값은 NULL입니다. 누락값을 0원으로 추정하거나 기존 경로에 소급 복원하지 않습니다. 요금이 필요하면 새로 조회해 별도 파일로 저장합니다.

카카오 비교창은 A/B 금액과 차액(B−A)을 표시하며 어느 한쪽 값이 없으면 비교 불가로 처리합니다. 통행료와 예상 택시요금은 서로 다른 지표이므로 합산하지 않습니다. 서비스별 조회 시점·경로·차량·할증 계산이 달라 실제 청구액이나 동일한 계산 조건을 보장하지 않습니다.

응답 필드의 의미는 [NAVER Directions 5 공식 문서](https://api.ncloud-docs.com/docs/application-maps-directions5)를 참고하세요.

## 검증 기록

개발 중 QGIS 3.44.14/4.2.2에서 합성 응답 → 메모리 이력 → GPKG/GeoJSON/SHP → 카카오 비교 UI를 오프라인 검증했습니다. 카카오 프로젝트의 `tests/qgis_fare_comparison_smoke.py`에 NAVER 프로젝트 경로를 전달해 재실행할 수 있습니다. 정확한 QGIS 3.34와 실제 API 응답을 사용하는 전체 수동 비교의 통과를 뜻하지 않습니다.
