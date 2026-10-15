# SPDX-License-Identifier: GPL-2.0-or-later
"""Ordered history fields and legacy Shapefile aliases; file schema stays unchanged."""

ROUTE_FIELDS = (('schema_ver', 'integer', 'schema_v', 'integer', None),
 ('history_id', 'string(36)', 'hist_id', 'string', 36),
 ('route_id', 'string(64)', 'route_id', 'string', 64),
 ('searched_at', 'string(32)', 'searched', 'string', 32),
 ('origin_lon', 'double', 'org_lon', 'double', None),
 ('origin_lat', 'double', 'org_lat', 'double', None),
 ('origin_name', 'string(255)', 'org_name', 'string', 254),
 ('destination_lon', 'double', 'dst_lon', 'double', None),
 ('destination_lat', 'double', 'dst_lat', 'double', None),
 ('destination_name', 'string(255)', 'dst_name', 'string', 254),
 ('waypoints_json', 'string(4096)', 'waypts', 'string', 254),
 ('distance_m', 'integer', 'dist_m', 'integer', None),
 ('duration_s', 'integer', 'dur_s', 'integer', None),
 ('guidance_count', 'integer', 'guide_cnt', 'integer', None),
 ('result_summary', 'string(255)', 'summary', 'string', 254),
 ('priority', 'string(16)', 'priority', 'string', 16),
 ('avoid', 'string(128)', 'avoid', 'string', 128),
 ('car_type', 'integer', 'car_type', 'integer', None),
 ('car_fuel', 'string(16)', 'car_fuel', 'string', 16),
 ('car_hipass', 'integer', 'car_hipass', 'integer', None),
 ('toll_fare', 'integer', 'toll_fare', 'integer', None),
 ('taxi_fare', 'integer', 'taxi_fare', 'integer', None))

GUIDANCE_FIELDS = (('schema_ver', 'integer', 'schema_v', 'integer', None),
 ('history_id', 'string(36)', 'hist_id', 'string', 36),
 ('route_id', 'string(64)', 'route_id', 'string', 64),
 ('searched_at', 'string(32)', 'searched', 'string', 32),
 ('sequence', 'integer', 'seq', 'integer', None),
 ('section_no', 'integer', 'sect_no', 'integer', None),
 ('guide_type', 'integer', 'g_type', 'integer', None),
 ('category', 'string(16)', 'category', 'string', 16),
 ('guidance', 'string(255)', 'guidance', 'string', 254),
 ('name', 'string(128)', 'name', 'string', 128),
 ('distance_m', 'integer', 'dist_m', 'integer', None),
 ('duration_s', 'integer', 'dur_s', 'integer', None),
 ('cum_distance_m', 'integer', 'cum_dist', 'integer', None),
 ('cum_duration_s', 'integer', 'cum_dur', 'integer', None),
 ('road_index', 'integer', 'road_idx', 'integer', None),
 ('longitude', 'double', 'lon', 'double', None),
 ('latitude', 'double', 'lat', 'double', None))


def history_fields(kind):
    if kind not in ("route", "guidance"):
        raise ValueError("Unknown history layer type")
    return ROUTE_FIELDS if kind == "route" else GUIDANCE_FIELDS


def history_memory_uri(kind):
    geometry = "LineString" if kind == "route" else "Point"
    return geometry + "?crs=EPSG:4326" + "".join(
        f"&field={name}:{memory_type}" for name, memory_type, *_ in history_fields(kind))


def history_shapefile_fields(kind):
    return [dict(source=name, name=short, type=export_type,
                 **({"length": length} if length is not None else {}))
            for name, _, short, export_type, length in history_fields(kind)]


def history_import_fields(kind):
    return [dict(source=name, name=short) for name, _, short, *_ in history_fields(kind)]
