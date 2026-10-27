# NAVER history and Kakao GPKG fare comparison

[한국어](fare-comparison.md) | English · [Home](../README.en.md) · [Save and export history](usage.en.md)

## Comparison workflow

1. Generate a new driving route in NAVER.
2. Save a GPKG using **경로 이력 GeoPackage 저장...** (“Save route history to GeoPackage...”) or an individual entry's Export command.
3. Open [Kakao QGIS Bridge](https://github.com/youngj-kim/kakao_qgis-bridge), with its comparison feature available, and select the NAVER file in **GPKG 경로 비교** (“GPKG route comparison”).
4. Select the routes to compare their distance, duration, toll, and estimated taxi fare.

The comparison window belongs to the Kakao plugin. The NAVER plugin does not provide a separate comparison window. Use GPKG for this workflow; GPX is not an input format for this comparison.

## Stored values and interpretation

| Value | NAVER response | History field |
| --- | --- | --- |
| Toll | `summary.tollFare` | `toll_fare` |
| Estimated taxi fare | `summary.taxiFare` | `taxi_fare` |

Amounts are preserved as integers in Korean won. Both fields survive GPKG/GeoJSON/SHP export and import. Older files with no fares retain NULL values; missing fares are neither treated as zero nor retroactively restored. Query a new route and save it separately if fares are required.

The Kakao comparison window shows A/B amounts and the difference (B−A). If either value is missing, that comparison is unavailable. Toll and estimated taxi fare are separate measures and are not added together. Query time, routes, vehicle assumptions, and surcharge calculations differ between services; neither actual charges nor identical calculation conditions are guaranteed.

See the [official NAVER Directions 5 documentation](https://api.ncloud-docs.com/docs/en/application-maps-directions5) for response field meanings.

## Verification record

During development, synthetic responses → memory history → GPKG/GeoJSON/SHP → Kakao comparison UI were verified offline on QGIS 3.44.14/4.2.2. To repeat, pass the NAVER project path to `tests/qgis_fare_comparison_smoke.py` in the Kakao project. This is not a complete manual comparison with exact QGIS 3.34 or live API responses.
