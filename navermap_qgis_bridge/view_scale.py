# SPDX-License-Identifier: GPL-2.0-or-later
"""Ground distances for viewport scale matching, independent of project CRS units."""
import math


def ground_distance(first, second):
    if not all(math.isfinite(value) for value in (*first, *second)):
        raise ValueError("Invalid ground coordinates")
    lon1, lat1 = map(math.radians, first)
    lon2, lat2 = map(math.radians, second)
    value = (math.sin((lat2 - lat1) / 2) ** 2
             + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 12742017.6 * math.asin(math.sqrt(max(0, min(1, value))))
