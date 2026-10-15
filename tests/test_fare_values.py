# SPDX-License-Identifier: GPL-2.0-or-later
import unittest
from navermap_qgis_bridge.fare_values import fare_amount, route_fares


class FareTests(unittest.TestCase):
    def test_missing_is_not_zero(self):
        self.assertEqual(route_fares({}), dict(toll_fare=None, taxi_fare=None))
        self.assertEqual(route_fares(dict(tollFare=0, taxiFare=10000)),
                         dict(toll_fare=0, taxi_fare=10000))
        self.assertEqual(route_fares(dict(tollFare=1200)),
                         dict(toll_fare=1200, taxi_fare=None))

    def test_malformed_optional_values_remain_unknown(self):
        for value in (True, -1, 0.5, "100", float("nan"), float("inf"), 10 ** 1000):
            with self.subTest(value=value), self.assertRaises(ValueError):
                fare_amount(value)
            self.assertIsNone(route_fares(dict(tollFare=value))["toll_fare"])
