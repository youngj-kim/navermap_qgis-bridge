# SPDX-License-Identifier: GPL-2.0-or-later
"""Optional KRW fares for route history and cross-provider GPKG comparison."""


def fare_amount(value):
    if value is None:
        return None
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not 0 <= value <= 2147483647 or value != int(value)):
        raise ValueError("요금은 원 단위의 0 이상 정수여야 합니다.")
    return int(value)


def route_fares(summary):
    result = {}
    for field, key in (("toll_fare", "tollFare"), ("taxi_fare", "taxiFare")):
        try:
            result[field] = fare_amount(summary.get(key))
        except ValueError:
            # Optional malformed fare must not become a false zero or break a route.
            result[field] = None
    return result
