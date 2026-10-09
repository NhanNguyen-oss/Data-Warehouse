"""
Stage S3 — Authority–year integration PoC.

Aggregate từng nguồn độc lập về grain (authority_code, year) rồi mới ghép, để
không join từng collision với từng count point (tránh fan-out nhân bản measure).

Mã authority chuẩn là mã mà DfT Traffic dùng trong năm đó (danh sách trong
local_authority_traffic.csv):
    - Collision dùng local_authority_highway (mã lúc xảy ra vụ), sau đó áp
      data/reference/authority_code_map.csv.
    - AADF có mã không hợp lệ trong năm đó được gán mã của chính count point ở
      năm gần nhất sau đó mà mã hợp lệ (count_point_later_code).

Đầu ra (commit làm bằng chứng):
    reports/poc/authority_year.csv          một dòng = một authority x year
    reports/poc/remap_audit.csv             mọi lần đổi mã, kèm số dòng bị ảnh hưởng
    reports/poc/RECONCILIATION.md           đối soát với raw, độ bao phủ, London

Cách chạy (chỉ cần thư viện chuẩn):
    python src/etl/authority_year.py
    python src/etl/authority_year.py --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import calendar
import csv
import logging
import sys
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

import profiling  # noqa: E402
import sources  # noqa: E402

ROOT = sources.ROOT
OUT_DIR = ROOT / "reports" / "poc"
CODE_MAP_PATH = ROOT / "data" / "reference" / "authority_code_map.csv"
DEFAULT_YEARS = profiling.DEFAULT_YEARS

MILES_TO_KM = 1.609344
PER_100M = 100_000_000
# first_road_class: 1 Motorway, 2 A(M), 3 A. Tương ứng mạng Major của DfT Traffic.
MAJOR_ROAD_CLASSES = {"1", "2", "3"}
UNMATCHED = "UNMATCHED"

OUTPUT_COLUMNS = [
    "authority_code", "authority_name", "year", "is_london",
    "collisions", "fatal_collisions", "serious_collisions", "slight_collisions",
    "severe_collision_share_pct", "adjusted_ksi_collisions", "injury_based_share_pct",
    "casualties", "major_road_collisions",
    "aadf_count_points", "aadf_counted_points", "aadf_estimated_share_pct",
    "aadf_mean_all_motor_vehicles", "aadf_major_points", "aadf_major_link_km", "aadf_major_vehicle_km",
    "la_network_km", "la_vehicle_km",
    "candidate_collisions_per_100m_vkm", "candidate_major_collisions_per_100m_major_vkm",
    "has_collisions", "has_aadf", "has_la_traffic",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("authority_year")


@dataclass(frozen=True)
class CodeRule:
    source: str
    from_code: str
    to_code: str
    year_from: int
    year_to: int
    reason: str


class CodeMap:
    def __init__(self, rules: Iterable[CodeRule]) -> None:
        self.rules = list(rules)

    @classmethod
    def load(cls, path: Path = CODE_MAP_PATH) -> CodeMap:
        with path.open(encoding="utf-8", newline="") as handle:
            return cls(
                CodeRule(row["source"], row["from_code"], row["to_code"],
                         int(row["year_from"]), int(row["year_to"]), row["reason"])
                for row in csv.DictReader(handle)
            )

    def apply(self, source: str, code: str, year: str) -> str:
        for rule in self.rules:
            if rule.source == source and rule.from_code == code and rule.year_from <= int(year) <= rule.year_to:
                return rule.to_code
        return code


@dataclass
class Audit:
    remaps: Counter = field(default_factory=Counter)
    unmatched: Counter = field(default_factory=Counter)

    def rows(self) -> list[tuple]:
        out = [(*key, count) for key, count in sorted(self.remaps.items())]
        out += [(source, year, code, UNMATCHED, method, count)
                for (source, year, code, method), count in sorted(self.unmatched.items())]
        return out


def pct(part: float, whole: float) -> float | None:
    return None if not whole else round(100.0 * part / whole, 2)


def rate(numerator: float, exposure: float) -> float | None:
    return None if not exposure else round(numerator / exposure * PER_100M, 3)


def days_in_year(year: str) -> int:
    return 366 if calendar.isleap(int(year)) else 365


# --------------------------------------------------------------------------- #
# Aggregate từng nguồn
# --------------------------------------------------------------------------- #
def aggregate_collisions(
    rows: Iterable[dict[str, str]], years: set[str], code_map: CodeMap,
    valid_codes: dict[str, set[str]], audit: Audit,
) -> tuple[dict[tuple[str, str], Counter], int]:
    totals: dict[tuple[str, str], Counter] = defaultdict(Counter)
    in_scope = 0
    for row in rows:
        year = row["collision_year"].strip()
        if year not in years:
            continue
        in_scope += 1
        original = row["local_authority_highway"].strip()
        code = code_map.apply("stats19", original, year)
        if code != original:
            audit.remaps[("stats19", year, original, code, "authority_code_map")] += 1
        if code not in valid_codes.get(year, ()):
            audit.unmatched[("stats19", year, original, "not_in_la_traffic")] += 1
            code = UNMATCHED
        bucket = totals[(code, year)]
        severity = row["collision_severity"].strip()
        bucket["collisions"] += 1
        bucket["fatal_collisions"] += severity == "1"
        bucket["serious_collisions"] += severity == "2"
        bucket["slight_collisions"] += severity == "3"
        bucket["adjusted_serious"] += profiling.to_float(row["collision_adjusted_severity_serious"]) or 0.0
        bucket["injury_based"] += row["collision_injury_based"].strip() == "1"
        bucket["casualties"] += profiling.to_int(row["number_of_casualties"]) or 0
        bucket["major_road_collisions"] += row["first_road_class"].strip() in MAJOR_ROAD_CLASSES
    return totals, in_scope


def later_valid_code(history: dict[str, str], year: str, valid_codes: dict[str, set[str]]) -> str | None:
    for later in sorted(y for y in history if y > year):
        code = history[later]
        if code in valid_codes.get(later, ()) and code in valid_codes.get(year, ()):
            return code
    return None


def aggregate_aadf(
    rows: Sequence[dict[str, str]], years: set[str], valid_codes: dict[str, set[str]], audit: Audit,
) -> tuple[dict[tuple[str, str], Counter], dict[str, str], int]:
    history: dict[str, dict[str, str]] = defaultdict(dict)
    for row in rows:
        history[row["count_point_id"].strip()][row["year"].strip()] = row["local_authority_code"].strip()

    totals: dict[tuple[str, str], Counter] = defaultdict(Counter)
    names: dict[str, str] = {}
    in_scope = 0
    for row in rows:
        year = row["year"].strip()
        if year not in years:
            continue
        in_scope += 1
        point = row["count_point_id"].strip()
        original = row["local_authority_code"].strip()
        code = original
        if code not in valid_codes.get(year, ()):
            remapped = later_valid_code(history[point], year, valid_codes)
            if remapped:
                audit.remaps[("aadf", year, original, remapped, "count_point_later_code")] += 1
                code = remapped
            else:
                audit.unmatched[("aadf", year, original, "no_valid_code_for_count_point")] += 1
                code = UNMATCHED
        else:
            names.setdefault(code, row["local_authority_name"].strip())
        bucket = totals[(code, year)]
        flow = profiling.to_int(row["all_motor_vehicles"]) or 0
        bucket["aadf_count_points"] += 1
        bucket["aadf_counted_points"] += row["estimation_method"].strip() == "Counted"
        bucket["aadf_flow_sum"] += flow
        length = profiling.to_float(row["link_length_km"])
        if row["road_type"].strip() == "Major" and length and length > 0:
            bucket["aadf_major_points"] += 1
            bucket["aadf_major_link_km"] += length
            bucket["aadf_major_vehicle_km"] += flow * length * days_in_year(year)
    return totals, names, in_scope


def aggregate_la_traffic(
    rows: Iterable[dict[str, str]], years: set[str],
) -> tuple[dict[tuple[str, str], dict], dict[str, str]]:
    totals: dict[tuple[str, str], dict] = {}
    names: dict[str, str] = {}
    for row in rows:
        year = row["year"].strip()
        if year not in years:
            continue
        code = row["local_authority_code"].strip()
        key = (code, year)
        if key in totals:
            raise ValueError(f"local_authority_traffic.csv trùng khóa {key}")
        names[code] = row["local_authority_name"].strip()
        miles = profiling.to_float(row["all_motor_vehicles"])
        totals[key] = {
            "la_network_km": profiling.to_float(row["link_length_km"]),
            "la_vehicle_km": None if miles is None else miles * MILES_TO_KM,
        }
    return totals, names


# --------------------------------------------------------------------------- #
# Ghép authority–year
# --------------------------------------------------------------------------- #
def combine(
    collisions: dict[tuple[str, str], Counter],
    aadf: dict[tuple[str, str], Counter],
    la_traffic: dict[tuple[str, str], dict],
    names: dict[str, str],
) -> list[dict]:
    keys = sorted(set(collisions) | set(aadf) | set(la_traffic), key=lambda k: (k[0], k[1]))
    output = []
    for code, year in keys:
        col = collisions.get((code, year), Counter())
        flow = aadf.get((code, year), Counter())
        la = la_traffic.get((code, year), {})
        n = col["collisions"]
        points = flow["aadf_count_points"]
        major_vkm = flow["aadf_major_vehicle_km"]
        la_vkm = la.get("la_vehicle_km")
        output.append({
            "authority_code": code,
            "authority_name": names.get(code, ""),
            "year": year,
            "is_london": int(profiling.is_london(code)),
            "collisions": n,
            "fatal_collisions": col["fatal_collisions"],
            "serious_collisions": col["serious_collisions"],
            "slight_collisions": col["slight_collisions"],
            "severe_collision_share_pct": pct(col["fatal_collisions"] + col["serious_collisions"], n),
            "adjusted_ksi_collisions": round(col["fatal_collisions"] + col["adjusted_serious"], 3) if n else 0,
            "injury_based_share_pct": pct(col["injury_based"], n),
            "casualties": col["casualties"],
            "major_road_collisions": col["major_road_collisions"],
            "aadf_count_points": points,
            "aadf_counted_points": flow["aadf_counted_points"],
            "aadf_estimated_share_pct": pct(points - flow["aadf_counted_points"], points),
            "aadf_mean_all_motor_vehicles": round(flow["aadf_flow_sum"] / points, 1) if points else None,
            "aadf_major_points": flow["aadf_major_points"],
            "aadf_major_link_km": round(flow["aadf_major_link_km"], 2),
            "aadf_major_vehicle_km": round(major_vkm),
            "la_network_km": la.get("la_network_km"),
            "la_vehicle_km": None if la_vkm is None else round(la_vkm),
            "candidate_collisions_per_100m_vkm": rate(n, la_vkm) if la_vkm else None,
            "candidate_major_collisions_per_100m_major_vkm": rate(col["major_road_collisions"], major_vkm),
            "has_collisions": int(n > 0),
            "has_aadf": int(points > 0),
            "has_la_traffic": int(bool(la)),
        })
    return output


def reconcile(
    output: list[dict], collisions_in_scope: int, aadf_in_scope: int, la_rows_in_scope: int, years: Sequence[str],
) -> dict:
    keys = [(row["authority_code"], row["year"]) for row in output]
    matched = [row for row in output if row["authority_code"] != UNMATCHED]
    exceed = [
        (row["authority_code"], row["year"])
        for row in matched
        if row["la_vehicle_km"] and row["aadf_major_vehicle_km"] > row["la_vehicle_km"]
    ]
    return {
        "duplicate_keys": len(keys) - len(set(keys)),
        "collisions_raw_in_scope": collisions_in_scope,
        "collisions_output": sum(row["collisions"] for row in output),
        "collisions_unmatched": sum(row["collisions"] for row in output if row["authority_code"] == UNMATCHED),
        "aadf_rows_raw_in_scope": aadf_in_scope,
        "aadf_rows_output": sum(row["aadf_count_points"] for row in output),
        "aadf_rows_unmatched": sum(row["aadf_count_points"] for row in output if row["authority_code"] == UNMATCHED),
        "la_traffic_rows_raw_in_scope": la_rows_in_scope,
        "la_traffic_rows_output": sum(row["has_la_traffic"] for row in output),
        "authority_years": len(matched),
        "expected_authority_years_from_la_traffic": la_rows_in_scope,
        "authority_years_missing_collisions": sorted(
            (r["authority_code"], r["year"]) for r in matched if not r["has_collisions"]),
        "authority_years_missing_aadf": sorted(
            (r["authority_code"], r["year"]) for r in matched if not r["has_aadf"]),
        "authority_years_missing_la_traffic": sorted(
            (r["authority_code"], r["year"]) for r in matched if not r["has_la_traffic"]),
        "aadf_major_vkm_exceeds_la_vkm": sorted(exceed),
        "years": list(years),
    }


# --------------------------------------------------------------------------- #
# Ghi đầu ra
# --------------------------------------------------------------------------- #
def write_csv(path: Path, columns: Sequence[str], rows: Iterable[Sequence]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)


def fmt(value) -> str:
    return profiling.fmt(value)


def render_markdown(run: dict, checks: dict, output: list[dict], audit_rows: list[tuple]) -> str:
    ok = lambda flag: "OK" if flag else "LỆCH"  # noqa: E731
    london = [row for row in output if row["is_london"]]
    lines = [
        "# Authority–year integration PoC (stage S3)",
        "",
        "File này do `python src/etl/authority_year.py` sinh ra. Không sửa tay; chạy lại để cập nhật.",
        "",
        f"- run_id: `{run['run_id']}`, xong lúc {run['finished_at_utc']}, {run['duration_seconds']} giây",
        f"- Năm: {', '.join(checks['years'])}",
        "- Nguồn (sha256):",
    ]
    lines += [f"  - `{info['path']}` `{info['sha256']}`" for info in run["sources"].values()]
    lines += [
        "",
        "## Phương pháp",
        "",
        "1. Mỗi nguồn được aggregate riêng về (authority_code, year), sau đó full outer join theo khóa này. Không có join collision × count point nên không có fan-out.",
        "2. Mã chuẩn là mã authority của DfT Traffic trong năm đó (danh sách trong `local_authority_traffic.csv`).",
        "3. Collision dùng `local_authority_highway` (mã lúc xảy ra vụ), áp `data/reference/authority_code_map.csv`.",
        "4. Dòng AADF có mã không hợp lệ trong năm được gán mã của cùng count point ở năm sau gần nhất (`count_point_later_code`).",
        "5. `aadf_mean_all_motor_vehicles` là trung bình của các count point được quan sát/ước tính, không phải lưu lượng toàn địa bàn.",
        "6. `aadf_major_vehicle_km` = Σ AADF × `link_length_km` × số ngày của năm (366 cho 2024), chỉ Major roads vì Minor không có link length.",
        "7. `la_vehicle_km` = vehicle miles toàn mạng trong `local_authority_traffic.csv` × 1,609344.",
        "8. Cột `candidate_*` là rate thử nghiệm để kiểm tra tính khả thi, **chưa bật** cho dashboard/DSS (D05, D07).",
        "",
        "## Đối soát",
        "",
        "| Kiểm tra | Raw | Output | Kết quả |",
        "|---|---|---|---|",
        f"| Khóa (authority_code, year) trùng | — | {fmt(checks['duplicate_keys'])} | {ok(checks['duplicate_keys'] == 0)} |",
        f"| Collisions | {fmt(checks['collisions_raw_in_scope'])} | {fmt(checks['collisions_output'])} | {ok(checks['collisions_raw_in_scope'] == checks['collisions_output'])} |",
        f"| AADF rows | {fmt(checks['aadf_rows_raw_in_scope'])} | {fmt(checks['aadf_rows_output'])} | {ok(checks['aadf_rows_raw_in_scope'] == checks['aadf_rows_output'])} |",
        f"| LA traffic rows | {fmt(checks['la_traffic_rows_raw_in_scope'])} | {fmt(checks['la_traffic_rows_output'])} | {ok(checks['la_traffic_rows_raw_in_scope'] == checks['la_traffic_rows_output'])} |",
        f"| Authority–year có mã hợp lệ | {fmt(checks['expected_authority_years_from_la_traffic'])} | {fmt(checks['authority_years'])} | {ok(checks['expected_authority_years_from_la_traffic'] == checks['authority_years'])} |",
        f"| Collisions không ghép được mã | — | {fmt(checks['collisions_unmatched'])} | {ok(checks['collisions_unmatched'] == 0)} |",
        f"| AADF rows không ghép được mã | — | {fmt(checks['aadf_rows_unmatched'])} | {ok(checks['aadf_rows_unmatched'] == 0)} |",
        f"| Major vehicle-km AADF > vehicle-km toàn mạng | — | {fmt(len(checks['aadf_major_vkm_exceeds_la_vkm']))} | {ok(not checks['aadf_major_vkm_exceeds_la_vkm'])} |",
        "",
        "Độ bao phủ (authority–year có mã hợp lệ nhưng thiếu một nguồn):",
        "",
        f"- Thiếu collisions: {', '.join(f'{c} {y}' for c, y in checks['authority_years_missing_collisions']) or 'không có'}",
        f"- Thiếu AADF: {', '.join(f'{c} {y}' for c, y in checks['authority_years_missing_aadf']) or 'không có'}",
        f"- Thiếu LA traffic: {', '.join(f'{c} {y}' for c, y in checks['authority_years_missing_la_traffic']) or 'không có'}",
        f"- Major vehicle-km AADF vượt toàn mạng: {', '.join(f'{c} {y}' for c, y in checks['aadf_major_vkm_exceeds_la_vkm']) or 'không có'}",
        "",
        "## Đổi mã (remap audit)",
        "",
        "| Nguồn | Năm | Mã gốc | Mã chuẩn | Phương pháp | Số dòng |",
        "|---|---|---|---|---|---|",
    ]
    lines += [f"| {s} | {y} | {a} | {b} | {m} | {fmt(n)} |" for s, y, a, b, m, n in audit_rows]
    lines += [
        "",
        "## London (33 authority, mã E09)",
        "",
        "| Năm | Authority | Collisions | Fatal + serious | Adjusted KSI collisions | Injury-based % | AADF count points | Estimated % | Major vehicle-km (tỷ) | Vehicle-km toàn mạng (tỷ) | Candidate collisions / 100M vkm |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for year in checks["years"]:
        rows = [row for row in london if row["year"] == year]
        if not rows:
            continue
        n = sum(r["collisions"] for r in rows)
        severe = sum(r["fatal_collisions"] + r["serious_collisions"] for r in rows)
        adjusted = sum(r["adjusted_ksi_collisions"] for r in rows)
        injury = sum((r["injury_based_share_pct"] or 0) * r["collisions"] / 100 for r in rows)
        points = sum(r["aadf_count_points"] for r in rows)
        counted = sum(r["aadf_counted_points"] for r in rows)
        major = sum(r["aadf_major_vehicle_km"] for r in rows)
        network = sum(r["la_vehicle_km"] or 0 for r in rows)
        lines.append(
            f"| {year} | {len(rows)} | {fmt(n)} | {fmt(severe)} | {fmt(round(adjusted, 1))} | {fmt(pct(injury, n))} "
            f"| {fmt(points)} | {fmt(pct(points - counted, points))} | {fmt(round(major / 1e9, 2))} "
            f"| {fmt(round(network / 1e9, 2))} | {fmt(rate(n, network))} |"
        )
    lines += [
        "",
        "## Giới hạn của PoC",
        "",
        "- Grain năm; không kết luận về giờ cao điểm hay tắc nghẽn.",
        "- Cumbria tách thành Cumberland và Westmorland and Furness từ 2023; chuỗi thời gian của ba mã này gãy tại 2023. Cần version history trong `dim_authority` (SCD Type 2) nếu muốn so sánh xuyên năm.",
        "- STATS19 chỉ gồm vụ có người bị thương được cảnh sát ghi nhận (under-reporting).",
        "- Severe share chịu ảnh hưởng của injury-based reporting; dùng `adjusted_ksi_collisions` khi so sánh giữa các năm.",
        "- Cờ `collision_injury_based` không phản ánh đúng hệ thống ghi nhận của mọi lực lượng: Metropolitan Police có cờ 0 cho 2021–2024 và 1 cho 2025, nhưng số serious hiệu chỉnh bằng số gốc ở mọi năm (DfT đã coi là injury-based). Không dùng cờ này làm chỉ báo chất lượng; dùng số hiệu chỉnh.",
        "- 64% bản ghi AADF là ước tính; LA traffic cũng là số ước tính của DfT.",
        "",
    ]
    return "\n".join(lines)


def read_rows(source_id: str, member: str | None = None) -> list[dict[str, str]] | Iterable[dict[str, str]]:
    return profiling.read_csv(sources.source_by_id(source_id).path, member)


def run(years: Sequence[str], out_dir: Path = OUT_DIR) -> dict:
    started = time.perf_counter()
    year_set = set(years)
    code_map = CodeMap.load()
    audit = Audit()

    la_rows = list(read_rows("traffic_local_authority"))
    la_traffic, la_names = aggregate_la_traffic(la_rows, year_set)
    valid_codes: dict[str, set[str]] = defaultdict(set)
    for code, year in la_traffic:
        valid_codes[year].add(code)

    collisions, collisions_in_scope = aggregate_collisions(
        read_rows("stats19_collision"), year_set, code_map, valid_codes, audit)
    aadf_rows = list(read_rows("traffic_aadf", "dft_traffic_counts_aadf.csv"))
    aadf, aadf_names, aadf_in_scope = aggregate_aadf(aadf_rows, year_set, valid_codes, audit)

    names = {**aadf_names, **la_names}
    output = combine(collisions, aadf, la_traffic, names)
    checks = reconcile(output, collisions_in_scope, aadf_in_scope, len(la_traffic), sorted(year_set))

    used = ("stats19_collision", "traffic_aadf", "traffic_local_authority")
    run_info = {
        "run_id": uuid.uuid4().hex[:12],
        "finished_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "duration_seconds": round(time.perf_counter() - started, 1),
        "sources": {
            s: {"path": f"data/raw/{sources.source_by_id(s).relative_path}", "sha256": sources.sha256_of(sources.source_by_id(s).path)}
            for s in used
        },
    }
    write_csv(out_dir / "authority_year.csv", OUTPUT_COLUMNS, ([row[c] for c in OUTPUT_COLUMNS] for row in output))
    audit_rows = audit.rows()
    write_csv(out_dir / "remap_audit.csv", ["source", "year", "from_code", "to_code", "method", "rows"], audit_rows)
    (out_dir / "RECONCILIATION.md").write_text(render_markdown(run_info, checks, output, audit_rows), encoding="utf-8")
    log.info("Ghi %s dòng authority–year vào %s (%s giây)", f"{len(output):,}", out_dir, run_info["duration_seconds"])
    return checks


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Authority–year integration PoC (STATS19 + DfT Traffic)")
    parser.add_argument("--years", nargs="+", default=list(DEFAULT_YEARS))
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    checks = run(args.years, args.out_dir)
    failed = (
        checks["duplicate_keys"]
        or checks["collisions_raw_in_scope"] != checks["collisions_output"]
        or checks["aadf_rows_raw_in_scope"] != checks["aadf_rows_output"]
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
