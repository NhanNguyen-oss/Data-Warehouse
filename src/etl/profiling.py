"""
Stage S2 — profiling tái lập cho STATS19 collision, DfT AADF, count points và
local authority traffic.

Mỗi lần chạy ghi:
    reports/profiling/profile.json      toàn bộ số liệu, kèm run_id, sha256 nguồn, bộ lọc
    reports/profiling/PROFILE.md        bản tóm tắt để đọc và dẫn vào báo cáo

Cách chạy (chỉ cần thư viện chuẩn; nguồn Traffic tải bằng src/etl/sources.py fetch):
    python src/etl/profiling.py
    python src/etl/profiling.py --years 2021 2022 2023 2024 2025
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import sys
import time
import uuid
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

import sources  # noqa: E402

ROOT = sources.ROOT
REPORT_DIR = ROOT / "reports" / "profiling"
DEFAULT_YEARS = ("2021", "2022", "2023", "2024", "2025")

LONDON_PREFIX = "E09"
LONDON_AUTHORITIES = 33
SENTINELS = ("", "-1")
GB_LON = (-9.0, 2.5)
GB_LAT = (49.0, 61.0)
SEVERITY_LABELS = {"1": "fatal", "2": "serious", "3": "slight"}

AADF_PARTS = ("two_wheeled_motor_vehicles", "cars_and_taxis", "buses_and_coaches", "LGVs", "all_HGVs")
HGV_PARTS = (
    "HGVs_2_rigid_axle", "HGVs_3_rigid_axle", "HGVs_4_or_more_rigid_axle",
    "HGVs_3_or_4_articulated_axle", "HGVs_5_articulated_axle", "HGVs_6_articulated_axle",
)
AADF_MEASURES = ("pedal_cycles", *AADF_PARTS, *HGV_PARTS, "all_motor_vehicles")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("profiling")


def pct(part: int, whole: int) -> float | None:
    return None if whole == 0 else round(100.0 * part / whole, 2)


def is_london(code: str) -> bool:
    return code.startswith(LONDON_PREFIX)


def to_int(text: str) -> int | None:
    try:
        return int(text)
    except (TypeError, ValueError):
        return None


def to_float(text: str) -> float | None:
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def sorted_dict(counter: dict) -> dict:
    return {key: counter[key] for key in sorted(counter)}


# --------------------------------------------------------------------------- #
# STATS19 collision
# --------------------------------------------------------------------------- #
def profile_collisions(rows: Iterable[dict[str, str]], years: set[str]) -> dict:
    total = 0
    in_scope = 0
    by_year: Counter[str] = Counter()
    seen: set[str] = set()
    duplicates = 0
    empty_key = 0
    bad_date = 0
    year_mismatch = 0
    bad_time = 0
    severity_by_year: dict[str, Counter[str]] = defaultdict(Counter)
    injury_based_by_year: Counter[str] = Counter()
    sentinel_counts: Counter[str] = Counter()
    columns: list[str] = []
    coord_missing = 0
    coord_outside_gb = 0
    highway_codes: dict[str, set[str]] = defaultdict(set)
    highway_current_codes: dict[str, set[str]] = defaultdict(set)
    highway_changed = 0
    highway_missing = 0
    london_by_year: Counter[str] = Counter()
    london_current_by_year: Counter[str] = Counter()
    london_severity: dict[str, Counter[str]] = defaultdict(Counter)
    road_class: Counter[str] = Counter()

    for row in rows:
        total += 1
        if not columns:
            columns = list(row)
        year = row["collision_year"].strip()
        by_year[year] += 1
        index = row["collision_index"].strip()
        if not index:
            empty_key += 1
        elif index in seen:
            duplicates += 1
        else:
            seen.add(index)
        if years and year not in years:
            continue
        in_scope += 1

        try:
            event_date = datetime.strptime(row["date"].strip(), "%d/%m/%Y")
            if str(event_date.year) != year:
                year_mismatch += 1
        except ValueError:
            bad_date += 1
        try:
            datetime.strptime(row["time"].strip(), "%H:%M")
        except ValueError:
            bad_time += 1

        for column in columns:
            if (row.get(column) or "").strip() in SENTINELS:
                sentinel_counts[column] += 1

        severity = row["collision_severity"].strip()
        severity_by_year[year][SEVERITY_LABELS.get(severity, f"other:{severity}")] += 1
        if row.get("collision_injury_based", "").strip() == "1":
            injury_based_by_year[year] += 1

        lon, lat = to_float(row["longitude"]), to_float(row["latitude"])
        if lon is None or lat is None:
            coord_missing += 1
        elif not (GB_LON[0] <= lon <= GB_LON[1] and GB_LAT[0] <= lat <= GB_LAT[1]):
            coord_outside_gb += 1

        highway = row["local_authority_highway"].strip()
        current = row["local_authority_highway_current"].strip()
        if highway in SENTINELS or current in SENTINELS:
            highway_missing += 1
        if highway not in SENTINELS:
            highway_codes[year].add(highway)
        if current not in SENTINELS:
            highway_current_codes[year].add(current)
        if highway != current:
            highway_changed += 1
        if is_london(highway):
            london_by_year[year] += 1
            london_severity[year][SEVERITY_LABELS.get(severity, "other")] += 1
        if is_london(current):
            london_current_by_year[year] += 1
        road_class[row["first_road_class"].strip()] += 1

    sentinel_share = {
        column: {"count": count, "pct": pct(count, in_scope)}
        for column, count in sorted(sentinel_counts.items(), key=lambda item: -item[1])
    }
    all_current = set().union(*highway_current_codes.values()) if highway_current_codes else set()
    return {
        "rows_total": total,
        "rows_in_scope": in_scope,
        "rows_by_collision_year": sorted_dict(by_year),
        "key": {
            "column": "collision_index",
            "empty": empty_key,
            "duplicates": duplicates,
            "unique": len(seen),
        },
        "date_unparseable": bad_date,
        "date_year_differs_from_collision_year": year_mismatch,
        "time_unparseable": bad_time,
        "severity_by_year": {year: sorted_dict(severity_by_year[year]) for year in sorted(severity_by_year)},
        "severe_share_by_year_pct": {
            year: pct(counts["fatal"] + counts["serious"], sum(counts.values()))
            for year, counts in sorted(severity_by_year.items())
        },
        "injury_based_share_by_year_pct": {
            year: pct(injury_based_by_year[year], sum(severity_by_year[year].values()))
            for year in sorted(severity_by_year)
        },
        "sentinel_empty_or_minus1": sentinel_share,
        "coordinates": {"missing": coord_missing, "outside_gb_bbox": coord_outside_gb},
        "highway_authority": {
            "missing": highway_missing,
            "rows_where_highway_differs_from_current": highway_changed,
            "distinct_highway_by_year": {y: len(c) for y, c in sorted(highway_codes.items())},
            "distinct_current_by_year": {y: len(c) for y, c in sorted(highway_current_codes.items())},
            "distinct_current_all_years": len(all_current),
        },
        "first_road_class": sorted_dict(road_class),
        "london": {
            "definition": f"local_authority_highway starts with {LONDON_PREFIX}",
            "collisions_by_year": sorted_dict(london_by_year),
            "collisions_total": sum(london_by_year.values()),
            "collisions_by_year_using_current_code": sorted_dict(london_current_by_year),
            "severity_by_year": {y: sorted_dict(london_severity[y]) for y in sorted(london_severity)},
            "distinct_authorities_current": len({c for c in all_current if is_london(c)}),
        },
        "_codes_current": {y: sorted(c) for y, c in sorted(highway_current_codes.items())},
        "_codes_at_event": {y: sorted(c) for y, c in sorted(highway_codes.items())},
    }


# --------------------------------------------------------------------------- #
# DfT AADF
# --------------------------------------------------------------------------- #
def profile_aadf(rows: Iterable[dict[str, str]], years: set[str]) -> dict:
    total = 0
    by_year: Counter[str] = Counter()
    keys: set[tuple[str, str]] = set()
    duplicates = 0
    in_scope = 0
    estimation: dict[str, Counter[str]] = defaultdict(Counter)
    estimation_detailed: Counter[str] = Counter()
    road_type: Counter[str] = Counter()
    road_category: Counter[str] = Counter()
    link_missing: dict[str, Counter[str]] = defaultdict(Counter)
    link_total: dict[str, Counter[str]] = defaultdict(Counter)
    measure_missing: Counter[str] = Counter()
    measure_negative: Counter[str] = Counter()
    all_mv_zero = 0
    total_mismatch = 0
    hgv_mismatch = 0
    total_gap: Counter[int] = Counter()
    points_by_year: dict[str, set[str]] = defaultdict(set)
    codes_by_year: dict[str, set[str]] = defaultdict(set)
    point_codes: dict[str, set[str]] = defaultdict(set)
    london_rows: Counter[str] = Counter()
    london_estimated: Counter[str] = Counter()
    london_link_missing: Counter[str] = Counter()
    london_points: dict[str, set[str]] = defaultdict(set)
    london_region_mismatch = 0
    all_points: set[str] = set()
    link_missing_all_years = 0

    for row in rows:
        total += 1
        year = row["year"].strip()
        point = row["count_point_id"].strip()
        by_year[year] += 1
        all_points.add(point)
        key = (point, year)
        if key in keys:
            duplicates += 1
        keys.add(key)
        length = to_float(row["link_length_km"])
        if length is None or length <= 0:
            link_missing_all_years += 1
        if years and year not in years:
            continue
        in_scope += 1

        method = row["estimation_method"].strip()
        estimation[year][method] += 1
        estimation_detailed[row["estimation_method_detailed"].strip()] += 1
        kind = row["road_type"].strip()
        road_type[kind] += 1
        road_category[row["road_category"].strip()] += 1
        link_total[year][kind] += 1
        if length is None or length <= 0:
            link_missing[year][kind] += 1

        values: dict[str, int | None] = {}
        for measure in AADF_MEASURES:
            value = to_int(row[measure].strip())
            values[measure] = value
            if value is None:
                measure_missing[measure] += 1
            elif value < 0:
                measure_negative[measure] += 1
        if values["all_motor_vehicles"] == 0:
            all_mv_zero += 1
        if all(values[m] is not None for m in (*AADF_PARTS, "all_motor_vehicles")):
            gap = values["all_motor_vehicles"] - sum(values[m] for m in AADF_PARTS)
            if gap:
                total_mismatch += 1
                total_gap[gap] += 1
        if all(values[m] is not None for m in (*HGV_PARTS, "all_HGVs")):
            if sum(values[m] for m in HGV_PARTS) != values["all_HGVs"]:
                hgv_mismatch += 1

        code = row["local_authority_code"].strip()
        points_by_year[year].add(point)
        codes_by_year[year].add(code)
        point_codes[point].add(code)
        if is_london(code):
            london_rows[year] += 1
            london_points[year].add(point)
            if method == "Estimated":
                london_estimated[year] += 1
            if length is None or length <= 0:
                london_link_missing[year] += 1
        if is_london(code) != (row["region_name"].strip() == "London"):
            london_region_mismatch += 1

    scope_years = sorted(points_by_year)
    panel = set.intersection(*(points_by_year[y] for y in scope_years)) if scope_years else set()
    london_panel = (
        set.intersection(*(london_points[y] for y in scope_years)) if scope_years and london_points else set()
    )
    estimated_total = sum(c["Estimated"] for c in estimation.values())
    link_missing_total = sum(sum(c.values()) for c in link_missing.values())
    london_total = sum(london_rows.values())
    return {
        "rows_total": total,
        "rows_in_scope": in_scope,
        "rows_by_year_all": sorted_dict(by_year),
        "year_range_all": [min(by_year), max(by_year)] if by_year else None,
        "count_points_all_years": len(all_points),
        "key": {"columns": ["count_point_id", "year"], "duplicates": duplicates, "unique": len(keys)},
        "estimation_method_by_year": {y: sorted_dict(estimation[y]) for y in sorted(estimation)},
        "estimated_share_pct": pct(estimated_total, in_scope),
        "estimated_share_by_year_pct": {
            y: pct(estimation[y]["Estimated"], sum(estimation[y].values())) for y in sorted(estimation)
        },
        "estimation_method_detailed": dict(estimation_detailed.most_common()),
        "road_type": sorted_dict(road_type),
        "road_category": sorted_dict(road_category),
        "link_length_missing_or_nonpositive": {
            "total": link_missing_total,
            "pct": pct(link_missing_total, in_scope),
            "all_years_total": link_missing_all_years,
            "all_years_pct": pct(link_missing_all_years, total),
            "by_year_and_road_type": {
                y: {k: {"missing": link_missing[y][k], "rows": link_total[y][k],
                        "pct": pct(link_missing[y][k], link_total[y][k])} for k in sorted(link_total[y])}
                for y in sorted(link_total)
            },
        },
        "measures": {
            "missing": sorted_dict(measure_missing),
            "negative": sorted_dict(measure_negative),
            "all_motor_vehicles_zero": all_mv_zero,
            "rows_where_parts_do_not_sum_to_all_motor_vehicles": total_mismatch,
            "all_motor_vehicles_minus_parts": {str(k): total_gap[k] for k in sorted(total_gap)},
            "rows_where_hgv_parts_do_not_sum_to_all_HGVs": hgv_mismatch,
        },
        "count_points_by_year": {y: len(points_by_year[y]) for y in scope_years},
        "count_points_present_every_scope_year": len(panel),
        "count_points_with_more_than_one_authority_code": sum(1 for c in point_codes.values() if len(c) > 1),
        "distinct_authorities_by_year": {y: len(codes_by_year[y]) for y in sorted(codes_by_year)},
        "london": {
            "definition": f"local_authority_code starts with {LONDON_PREFIX}",
            "rows_by_year": sorted_dict(london_rows),
            "rows_total": london_total,
            "estimated_share_pct": pct(sum(london_estimated.values()), london_total),
            "estimated_share_by_year_pct": {y: pct(london_estimated[y], london_rows[y]) for y in sorted(london_rows)},
            "link_length_missing_pct": pct(sum(london_link_missing.values()), london_total),
            "count_points_by_year": {y: len(london_points[y]) for y in sorted(london_points)},
            "count_points_present_every_scope_year": len(london_panel),
            "rows_where_E09_and_region_name_disagree": london_region_mismatch,
        },
        "_codes": {y: sorted(c) for y, c in sorted(codes_by_year.items())},
        "_points": sorted(all_points),
    }


def profile_count_points(rows: Iterable[dict[str, str]]) -> dict:
    total = 0
    ids: Counter[str] = Counter()
    years: Counter[str] = Counter()
    road_type: Counter[str] = Counter()
    link_missing = 0
    coord_missing = 0
    london = 0
    for row in rows:
        total += 1
        ids[row["count_point_id"].strip()] += 1
        years[row["year"].strip()] += 1
        road_type[row["road_type"].strip()] += 1
        length = to_float(row["link_length_km"])
        if length is None or length <= 0:
            link_missing += 1
        if to_float(row["latitude"]) is None or to_float(row["longitude"]) is None:
            coord_missing += 1
        if is_london(row["local_authority_code"].strip()):
            london += 1
    return {
        "rows_total": total,
        "key": {"column": "count_point_id", "duplicates": sum(c - 1 for c in ids.values() if c > 1), "unique": len(ids)},
        "metadata_year": sorted_dict(years),
        "road_type": sorted_dict(road_type),
        "link_length_missing_or_nonpositive": {"count": link_missing, "pct": pct(link_missing, total)},
        "coordinates_missing": coord_missing,
        "london_points": london,
        "_ids": sorted(ids),
    }


def profile_la_traffic(rows: Iterable[dict[str, str]], years: set[str]) -> dict:
    total = 0
    keys: set[tuple[str, str]] = set()
    duplicates = 0
    by_year: Counter[str] = Counter()
    codes_by_year: dict[str, set[str]] = defaultdict(set)
    missing: Counter[str] = Counter()
    scientific = 0
    for row in rows:
        total += 1
        year = row["year"].strip()
        code = row["local_authority_code"].strip()
        if any("e" in row[c].lower() for c in ("cars_and_taxis", "all_motor_vehicles")):
            scientific += 1
        by_year[year] += 1
        key = (code, year)
        if key in keys:
            duplicates += 1
        keys.add(key)
        if years and year not in years:
            continue
        codes_by_year[year].add(code)
        for column in ("link_length_km", "cars_and_taxis", "all_motor_vehicles"):
            if to_float(row[column]) is None:
                missing[column] += 1
    return {
        "rows_total": total,
        "key": {"columns": ["local_authority_code", "year"], "duplicates": duplicates},
        "year_range_all": [min(by_year), max(by_year)] if by_year else None,
        "rows_by_year_in_scope": {y: by_year[y] for y in sorted(codes_by_year)},
        "missing_in_scope": sorted_dict(missing),
        "rows_with_scientific_notation": scientific,
        "unit_note": "all_motor_vehicles và cars_and_taxis là vehicle miles/năm theo tên cột nguồn; cần đối chiếu metadata DfT",
        "london_authorities_by_year": {y: sum(1 for c in codes if is_london(c)) for y, codes in sorted(codes_by_year.items())},
        "_codes": {y: sorted(c) for y, c in sorted(codes_by_year.items())},
    }


# --------------------------------------------------------------------------- #
# Đối chiếu giữa các nguồn
# --------------------------------------------------------------------------- #
def cross_source(collision: dict, aadf: dict, count_points: dict, la_traffic: dict) -> dict:
    aadf_codes = aadf["_codes"]
    la_codes = la_traffic["_codes"]
    common_years = sorted(set(collision["_codes_current"]) & set(aadf_codes) & set(la_codes))
    aadf_points = set(aadf["_points"])
    meta_points = set(count_points["_ids"])
    return {
        "common_years": common_years,
        "authority_codes_by_year": compare_codes(collision["_codes_current"], aadf_codes, la_codes, common_years),
        "authority_codes_by_year_at_event": compare_codes(collision["_codes_at_event"], aadf_codes, la_codes, common_years),
        "aadf_points_missing_from_count_points": len(aadf_points - meta_points),
        "count_points_without_aadf": len(meta_points - aadf_points),
    }


def compare_codes(stats_codes: dict, aadf_codes: dict, la_codes: dict, common_years: list[str]) -> dict:
    by_year = {}
    for year in common_years:
        stats_set = set(stats_codes.get(year, ()))
        aadf_set = set(aadf_codes[year])
        la_set = set(la_codes[year])
        by_year[year] = {
            "stats19": len(stats_set),
            "aadf": len(aadf_set),
            "la_traffic": len(la_set),
            "stats19_not_in_aadf": sorted(stats_set - aadf_set),
            "aadf_not_in_stats19": sorted(aadf_set - stats_set),
            "stats19_not_in_la_traffic": sorted(stats_set - la_set),
            "la_traffic_not_in_stats19": sorted(la_set - stats_set),
            "london": {
                "stats19": len({c for c in stats_set if is_london(c)}),
                "aadf": len({c for c in aadf_set if is_london(c)}),
                "la_traffic": len({c for c in la_set if is_london(c)}),
                "matched_all_three": len({c for c in stats_set & aadf_set & la_set if is_london(c)}),
                "expected": LONDON_AUTHORITIES,
            },
        }
    return by_year


# --------------------------------------------------------------------------- #
# Đọc nguồn và ghi báo cáo
# --------------------------------------------------------------------------- #
def read_csv(path: Path, member: str | None = None) -> Iterator[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Thiếu {path}. Chạy: python src/etl/sources.py fetch")
    log.info("Đọc %s%s", path.name, f"::{member}" if member else "")
    if member:
        with zipfile.ZipFile(path) as archive, archive.open(member) as raw:
            yield from csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
    else:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            yield from csv.DictReader(handle)


def strip_private(value):
    if isinstance(value, dict):
        return {k: strip_private(v) for k, v in value.items() if not k.startswith("_")}
    return value


def run_profile(years: Sequence[str]) -> dict:
    started = time.perf_counter()
    year_set = set(years)
    used = ("stats19_collision", "traffic_aadf", "traffic_count_points", "traffic_local_authority")
    fingerprints = {
        source_id: {"path": f"data/raw/{sources.source_by_id(source_id).relative_path}",
                    "sha256": sources.sha256_of(sources.source_by_id(source_id).path)}
        for source_id in used
        if sources.source_by_id(source_id).path.exists()
    }
    collision = profile_collisions(read_csv(sources.source_by_id("stats19_collision").path), year_set)
    aadf = profile_aadf(read_csv(sources.source_by_id("traffic_aadf").path, "dft_traffic_counts_aadf.csv"), year_set)
    count_points = profile_count_points(read_csv(sources.source_by_id("traffic_count_points").path, "count_points.csv"))
    la_traffic = profile_la_traffic(read_csv(sources.source_by_id("traffic_local_authority").path), year_set)
    cross = cross_source(collision, aadf, count_points, la_traffic)
    return {
        "run": {
            "run_id": uuid.uuid4().hex[:12],
            "finished_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "duration_seconds": round(time.perf_counter() - started, 1),
            "python": sys.version.split()[0],
            "filters": {"years": sorted(year_set)},
            "sources": fingerprints,
        },
        "stats19_collision": strip_private(collision),
        "traffic_aadf": strip_private(aadf),
        "traffic_count_points": strip_private(count_points),
        "traffic_local_authority": strip_private(la_traffic),
        "cross_source": cross,
        "release_status": {
            "stats19": "Không xác định được từ file: data guide không ghi provisional/final. README ghi bản 'last 5 years' chính thức cho 2025; cần đối chiếu trang DfT.",
            "traffic": "Không xác định được từ file; member trong zip ghi ngày 2026-06-02. Cần đối chiếu trang roadtraffic.dft.gov.uk.",
        },
    }


def fmt(value) -> str:
    if isinstance(value, int):
        return f"{value:,}".replace(",", ".")
    if isinstance(value, float):
        return f"{value:.2f}".replace(".", ",")
    return "—" if value is None else str(value)


def render_markdown(profile: dict) -> str:
    run = profile["run"]
    col = profile["stats19_collision"]
    aadf = profile["traffic_aadf"]
    cp = profile["traffic_count_points"]
    la = profile["traffic_local_authority"]
    cross = profile["cross_source"]
    years = run["filters"]["years"]
    lines = [
        "# Profiling report (stage S2)",
        "",
        "File này do `python src/etl/profiling.py` sinh ra. Không sửa tay; chạy lại để cập nhật.",
        "",
        f"- run_id: `{run['run_id']}`, xong lúc {run['finished_at_utc']}, {run['duration_seconds']} giây, Python {run['python']}",
        f"- Bộ lọc năm: {', '.join(years) if years else 'không lọc'}",
        "- Nguồn (sha256):",
    ]
    lines += [f"  - `{info['path']}` `{info['sha256']}`" for info in run["sources"].values()]

    lines += [
        "",
        "## STATS19 collision",
        "",
        f"- Tổng bản ghi {fmt(col['rows_total'])}, trong phạm vi năm {fmt(col['rows_in_scope'])}.",
        f"- `collision_index`: {fmt(col['key']['unique'])} giá trị duy nhất, {fmt(col['key']['duplicates'])} trùng, {fmt(col['key']['empty'])} rỗng.",
        f"- Ngày không đọc được {fmt(col['date_unparseable'])}; năm của `date` khác `collision_year` {fmt(col['date_year_differs_from_collision_year'])}; giờ không đọc được {fmt(col['time_unparseable'])}.",
        f"- Tọa độ thiếu {fmt(col['coordinates']['missing'])}, nằm ngoài khung GB {fmt(col['coordinates']['outside_gb_bbox'])}.",
        f"- Highway authority thiếu {fmt(col['highway_authority']['missing'])}; dòng có `local_authority_highway` khác `_current` {fmt(col['highway_authority']['rows_where_highway_differs_from_current'])}.",
        "",
        "| Năm | Vụ | Fatal | Serious | Slight | Severe share % | Injury-based % | Highway authority (current) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for year, counts in col["severity_by_year"].items():
        lines.append(
            f"| {year} | {fmt(sum(counts.values()))} | {fmt(counts.get('fatal', 0))} | {fmt(counts.get('serious', 0))} "
            f"| {fmt(counts.get('slight', 0))} | {fmt(col['severe_share_by_year_pct'][year])} "
            f"| {fmt(col['injury_based_share_by_year_pct'][year])} | {fmt(col['highway_authority']['distinct_current_by_year'][year])} |"
        )
    lines += [
        "",
        "Severe share theo collision severity bị ảnh hưởng bởi việc chuyển sang hệ thống ghi nhận dựa trên thương tích (cột Injury-based). Không so sánh giữa các năm nếu chưa hiệu chỉnh.",
        "",
        "Cột có tỷ lệ rỗng hoặc `-1` cao nhất (trong phạm vi năm):",
        "",
        "| Cột | Số dòng | % |",
        "|---|---|---|",
    ]
    for column, info in list(col["sentinel_empty_or_minus1"].items())[:12]:
        lines.append(f"| `{column}` | {fmt(info['count'])} | {fmt(info['pct'])} |")

    london = col["london"]
    lines += [
        "",
        f"London ({london['definition']}): {fmt(london['collisions_total'])} vụ trong phạm vi năm, "
        f"{fmt(london['distinct_authorities_current'])} authority theo mã current.",
        "",
        "| Năm | Vụ (mã lúc xảy ra) | Vụ (mã current) |",
        "|---|---|---|",
    ]
    for year in london["collisions_by_year"]:
        lines.append(f"| {year} | {fmt(london['collisions_by_year'][year])} | {fmt(london['collisions_by_year_using_current_code'].get(year, 0))} |")

    link = aadf["link_length_missing_or_nonpositive"]
    lines += [
        "",
        "## DfT AADF",
        "",
        f"- Tổng bản ghi {fmt(aadf['rows_total'])} (năm {aadf['year_range_all'][0]}–{aadf['year_range_all'][1]}), {fmt(aadf['count_points_all_years'])} count point; trong phạm vi năm {fmt(aadf['rows_in_scope'])}.",
        f"- Khóa (`count_point_id`, `year`): {fmt(aadf['key']['duplicates'])} trùng trên toàn file.",
        f"- Estimated chiếm {fmt(aadf['estimated_share_pct'])}% bản ghi trong phạm vi năm.",
        f"- `link_length_km` thiếu hoặc ≤ 0: {fmt(link['total'])} bản ghi ({fmt(link['pct'])}%) trong phạm vi năm; {fmt(link['all_years_total'])} ({fmt(link['all_years_pct'])}%) trên toàn file.",
        f"- Thành phần không cộng ra `all_motor_vehicles`: {fmt(aadf['measures']['rows_where_parts_do_not_sum_to_all_motor_vehicles'])} "
        f"(phân bố `all_motor_vehicles` − tổng thành phần: {', '.join(f'{k}: {fmt(v)}' for k, v in aadf['measures']['all_motor_vehicles_minus_parts'].items())}); "
        f"HGV con không cộng ra `all_HGVs`: {fmt(aadf['measures']['rows_where_hgv_parts_do_not_sum_to_all_HGVs'])}; `all_motor_vehicles` = 0: {fmt(aadf['measures']['all_motor_vehicles_zero'])}.",
        f"- Count point có mặt ở mọi năm trong phạm vi: {fmt(aadf['count_points_present_every_scope_year'])}; count point đổi mã authority giữa các năm (toàn file): {fmt(aadf['count_points_with_more_than_one_authority_code'])}.",
        "",
        "| Năm | Bản ghi | Count point | Estimated % | Link length thiếu (Major) | Link length thiếu (Minor) | Authority |",
        "|---|---|---|---|---|---|---|",
    ]
    for year in aadf["estimation_method_by_year"]:
        by_type = link["by_year_and_road_type"][year]
        major = by_type.get("Major", {})
        minor = by_type.get("Minor", {})
        lines.append(
            f"| {year} | {fmt(sum(aadf['estimation_method_by_year'][year].values()))} | {fmt(aadf['count_points_by_year'][year])} "
            f"| {fmt(aadf['estimated_share_by_year_pct'][year])} | {fmt(major.get('pct'))}% | {fmt(minor.get('pct'))}% "
            f"| {fmt(aadf['distinct_authorities_by_year'][year])} |"
        )
    al = aadf["london"]
    lines += [
        "",
        f"London ({al['definition']}): {fmt(al['rows_total'])} bản ghi, Estimated {fmt(al['estimated_share_pct'])}%, "
        f"link length thiếu {fmt(al['link_length_missing_pct'])}%, {fmt(al['count_points_present_every_scope_year'])} count point có mặt mọi năm. "
        f"Dòng mà mã E09 và `region_name = London` không khớp: {fmt(al['rows_where_E09_and_region_name_disagree'])}.",
        "",
        "Phương pháp ước tính chi tiết (trong phạm vi năm):",
        "",
    ]
    lines += [f"- {name}: {fmt(count)}" for name, count in aadf["estimation_method_detailed"].items()]

    lines += [
        "",
        "## Count points và local authority traffic",
        "",
        f"- `count_points.csv`: {fmt(cp['rows_total'])} dòng, {fmt(cp['key']['duplicates'])} `count_point_id` trùng, năm metadata {', '.join(cp['metadata_year'])}; link length thiếu {fmt(cp['link_length_missing_or_nonpositive']['pct'])}%.",
        f"- AADF count point không có trong `count_points.csv`: {fmt(cross['aadf_points_missing_from_count_points'])}; count point không có AADF: {fmt(cross['count_points_without_aadf'])}.",
        f"- `local_authority_traffic.csv`: {fmt(la['rows_total'])} dòng, năm {la['year_range_all'][0]}–{la['year_range_all'][1]}, khóa (`local_authority_code`, `year`) trùng {fmt(la['key']['duplicates'])}; giá trị thiếu trong phạm vi năm: {la['missing_in_scope'] or 'không có'}; "
        f"dòng ghi số dạng khoa học (ví dụ `1.245e+09`): {fmt(la['rows_with_scientific_notation'])}.",
        "",
        "## Đối chiếu mã authority giữa ba nguồn",
        "",
        f"Năm chung: {', '.join(cross['common_years'])}.",
    ]
    variants = (
        ("authority_codes_by_year", "STATS19 dùng `local_authority_highway_current`"),
        ("authority_codes_by_year_at_event", "STATS19 dùng `local_authority_highway` (mã lúc xảy ra vụ)"),
    )
    for key, caption in variants:
        lines += [
            "",
            f"{caption}:",
            "",
            "| Năm | STATS19 | AADF | LA traffic | STATS19 thiếu trong AADF | AADF thiếu trong STATS19 | STATS19 thiếu trong LA traffic | LA traffic thiếu trong STATS19 | London khớp cả ba / 33 |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for year, info in cross[key].items():
            lines.append(
                f"| {year} | {info['stats19']} | {info['aadf']} | {info['la_traffic']} "
                f"| {', '.join(info['stats19_not_in_aadf']) or '—'} | {', '.join(info['aadf_not_in_stats19']) or '—'} "
                f"| {', '.join(info['stats19_not_in_la_traffic']) or '—'} | {', '.join(info['la_traffic_not_in_stats19']) or '—'} "
                f"| {info['london']['matched_all_three']} |"
            )
    lines += [
        "",
        "## Trạng thái bản phát hành",
        "",
        f"- STATS19: {profile['release_status']['stats19']}",
        f"- Traffic: {profile['release_status']['traffic']}",
        "",
    ]
    return "\n".join(lines)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profiling nguồn STATS19 và DfT Traffic")
    parser.add_argument("--years", nargs="*", default=list(DEFAULT_YEARS), help="năm trong phạm vi; để trống = mọi năm")
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    profile = run_profile(args.years)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "profile.json").write_text(
        json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (args.out_dir / "PROFILE.md").write_text(render_markdown(profile), encoding="utf-8")
    log.info("Ghi %s và PROFILE.md (%s giây)", args.out_dir / "profile.json", profile["run"]["duration_seconds"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
