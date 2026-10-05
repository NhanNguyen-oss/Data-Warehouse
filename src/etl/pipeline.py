"""
CO4031 | ETL nạp dữ liệu tai nạn giao thông STATS19 (DfT, 2021–2025) vào kho dữ liệu.

Nguồn trong data/raw/:
    dft-road-casualty-statistics-collision-last-5-years.csv   một dòng = một vụ va chạm
    dft-road-casualty-statistics-vehicle-last-5-years.csv     một dòng = một xe trong một vụ
    dft-road-casualty-statistics-casualty-last-5-years.csv    một dòng = một nạn nhân
    dft-road-casualty-statistics-road-safety-open-dataset-data-guide-2025.xlsx
                                                              bảng tra mã -> nhãn chính thức

Đích: các bảng dw.* trong src/database/schema.sql.
Load luôn ghi mỗi bảng ra data/processed/<bảng>.csv cùng etl_report.csv (số liệu đối soát).
Thêm --load để COPY các CSV đó vào PostgreSQL.

Cách chạy (chỉ cần thư viện chuẩn; --load cần thêm: pip install "psycopg[binary]"):
    python src/etl/pipeline.py                   toàn bộ 5 năm
    python src/etl/pipeline.py --years 2025      chỉ các năm chỉ định
    python src/etl/pipeline.py --limit 5000      5000 vụ đầu tiên cùng xe và nạn nhân của chúng
    python src/etl/pipeline.py --load            nạp PostgreSQL, chuỗi kết nối lấy từ DW_DATABASE_URL
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Iterator, NamedTuple, Sequence

for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure is not None:
        _reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "processed"

COLLISION_FILE = "dft-road-casualty-statistics-collision-last-5-years.csv"
VEHICLE_FILE = "dft-road-casualty-statistics-vehicle-last-5-years.csv"
CASUALTY_FILE = "dft-road-casualty-statistics-casualty-last-5-years.csv"
GUIDE_FILE = "dft-road-casualty-statistics-road-safety-open-dataset-data-guide-2025.xlsx"
GUIDE_SHEET = "2024_code_list"

UNKNOWN_CODE = -1
UNKNOWN_TEXT = "UNKNOWN"
UNKNOWN_LABEL = "Data missing or out of range"
SEVERITY_CODES = (1, 2, 3)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("etl")

# --------------------------------------------------------------------------- #
# Cột của từng bảng — phải khớp tên cột trong src/database/schema.sql
# --------------------------------------------------------------------------- #
ROAD_FIELDS = (
    "first_road_class",
    "road_type",
    "junction_detail",
    "junction_control",
    "second_road_class",
    "pedestrian_crossing",
    "trunk_road_flag",
)
CONDITION_FIELDS = (
    "light_conditions",
    "weather_conditions",
    "road_surface_conditions",
    "special_conditions_at_site",
    "carriageway_hazards",
)
VEHICLE_FIELDS = (
    "vehicle_type",
    "propulsion_code",
    "towing_and_articulation",
    "vehicle_left_hand_drive",
    "escooter_flag",
)
DRIVER_FIELDS = (
    "sex_of_driver",
    "age_band_of_driver",
    "driver_imd_decile",
    "journey_purpose_of_driver",
)
ACTION_FIELDS = (
    "vehicle_manoeuvre",
    "junction_location",
    "skidding_and_overturning",
    "hit_object_in_carriageway",
    "vehicle_leaving_carriageway",
    "hit_object_off_carriageway",
    "first_point_of_impact",
)
CASUALTY_FIELDS = (
    "casualty_class",
    "sex_of_casualty",
    "age_band_of_casualty",
    "casualty_type",
    "casualty_imd_decile",
    "pedestrian_location",
    "pedestrian_movement",
    "car_passenger",
    "bus_or_coach_passenger",
    "escooter_flag",
)


def coded_columns(fields: Sequence[str]) -> list[str]:
    return [name for field in fields for name in (field, f"{field}_label")]


DATE_COLUMNS = [
    "date_key", "full_date", "day_of_month", "day_of_week", "day_name", "is_weekend",
    "week_of_year", "month_number", "month_name", "quarter", "year",
]
TIME_COLUMNS = ["time_key", "hour", "minute", "time_band", "is_peak_hour"]
SEVERITY_COLUMNS = ["severity_key", "severity_label"]
LOCATION_COLUMNS = [
    "police_force", "police_force_label",
    "local_authority_ons_district", "local_authority_ons_district_label",
    "local_authority_highway", "local_authority_highway_label",
    "lsoa_code",
    "urban_or_rural_area", "urban_or_rural_area_label",
]
ROAD_COLUMNS = coded_columns(ROAD_FIELDS) + ["speed_limit"]
CONDITION_COLUMNS = coded_columns(CONDITION_FIELDS)
VEHICLE_COLUMNS = coded_columns(VEHICLE_FIELDS) + ["engine_capacity_band", "vehicle_age_band"]
DRIVER_COLUMNS = coded_columns(DRIVER_FIELDS)
ACTION_COLUMNS = coded_columns(ACTION_FIELDS)
CASUALTY_COLUMNS = coded_columns(CASUALTY_FIELDS)

FACT_COLLISION_COLUMNS = [
    "collision_key", "collision_index", "date_key", "time_key", "location_key", "road_key",
    "conditions_key", "severity_key", "number_of_vehicles", "number_of_casualties",
    "fatal_count", "serious_count", "slight_count", "adjusted_serious", "adjusted_slight",
    "injury_based_reporting", "police_attended", "longitude", "latitude",
]
FACT_VEHICLE_COLUMNS = [
    "vehicle_fact_key", "collision_index", "vehicle_reference", "date_key", "time_key",
    "location_key", "road_key", "conditions_key", "collision_severity_key", "vehicle_key",
    "driver_key", "action_key", "vehicle_count", "age_of_driver", "engine_capacity_cc",
    "age_of_vehicle",
]
FACT_CASUALTY_COLUMNS = [
    "casualty_fact_key", "collision_index", "vehicle_reference", "casualty_reference",
    "date_key", "time_key", "location_key", "road_key", "conditions_key", "severity_key",
    "casualty_profile_key", "vehicle_key", "casualty_count", "fatal_count", "serious_count",
    "slight_count", "adjusted_serious", "adjusted_slight", "age_of_casualty",
]

# Thứ tự nạp: dimension trước, fact sau (theo khóa ngoại).
LOAD_ORDER = (
    "dim_date", "dim_time", "dim_severity", "dim_location", "dim_road", "dim_conditions",
    "dim_vehicle", "dim_driver", "dim_vehicle_action", "dim_casualty",
    "fact_collision", "fact_vehicle", "fact_casualty",
)

DAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
TIME_BANDS = (
    (0, 5, "Night (00-05)"),
    (6, 9, "Morning peak (06-09)"),
    (10, 15, "Daytime (10-15)"),
    (16, 19, "Evening peak (16-19)"),
    (20, 23, "Evening (20-23)"),
)
PEAK_BANDS = {"Morning peak (06-09)", "Evening peak (16-19)"}


# --------------------------------------------------------------------------- #
# Đọc và chuẩn hóa giá trị
# --------------------------------------------------------------------------- #
def parse_code(raw: str | None) -> int:
    """Mã số STATS19. Rỗng hoặc không phải số -> -1 (thiếu dữ liệu)."""
    try:
        return int((raw or "").strip())
    except ValueError:
        return UNKNOWN_CODE


def parse_text_code(raw: str | None) -> str:
    """Mã dạng chuỗi (quận huyện, LSOA). Rỗng hoặc -1 -> UNKNOWN."""
    text = (raw or "").strip()
    return text if text and text != "-1" else UNKNOWN_TEXT


def parse_measure(raw: str | None) -> int | None:
    """Số đo nguyên (tuổi, dung tích). Giá trị âm là mã thiếu dữ liệu -> NULL."""
    value = parse_code(raw)
    return None if value < 0 else value


def parse_decimal_text(raw: str | None) -> str:
    """Giữ nguyên chuỗi số thập phân để không mất độ chính xác; không hợp lệ -> NULL."""
    text = (raw or "").strip()
    try:
        float(text)
    except ValueError:
        return ""
    return text


def parse_time_key(raw: str | None) -> int:
    try:
        moment = datetime.strptime((raw or "").strip(), "%H:%M")
    except ValueError:
        return UNKNOWN_CODE
    return moment.hour * 100 + moment.minute


def date_key(day: date) -> int:
    return day.year * 10000 + day.month * 100 + day.day


def severity_flags(severity: int) -> tuple[int, int, int]:
    return int(severity == 1), int(severity == 2), int(severity == 3)


def engine_capacity_band(cc: int | None) -> str:
    if not cc:
        return "Unknown"
    if cc <= 125:
        return "<=125cc"
    if cc < 1000:
        return "126-999cc"
    if cc < 1600:
        return "1000-1599cc"
    if cc < 2000:
        return "1600-1999cc"
    return "2000cc+"


def vehicle_age_band(years: int | None) -> str:
    if years is None:
        return "Unknown"
    if years <= 2:
        return "0-2 years"
    if years <= 5:
        return "3-5 years"
    if years <= 10:
        return "6-10 years"
    if years <= 15:
        return "11-15 years"
    return "16+ years"


# --------------------------------------------------------------------------- #
# Bảng tra mã của DfT (xlsx) — đọc bằng thư viện chuẩn, không cần openpyxl
# --------------------------------------------------------------------------- #
_XLSX_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_XLSX_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def read_xlsx_rows(path: Path, sheet_name: str) -> Iterator[dict[str, str]]:
    """Trả mỗi dòng của một sheet dưới dạng {chữ cột: giá trị}."""
    with zipfile.ZipFile(path) as book:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in book.namelist():
            root = ET.fromstring(book.read("xl/sharedStrings.xml"))
            shared = [
                "".join(node.text or "" for node in item.iter(f"{_XLSX_MAIN}t"))
                for item in root.findall(f"{_XLSX_MAIN}si")
            ]
        workbook = ET.fromstring(book.read("xl/workbook.xml"))
        relations = ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
        targets = {rel.get("Id"): rel.get("Target", "") for rel in relations}
        rel_id = next(
            (
                sheet.get(f"{_XLSX_REL}id")
                for sheet in workbook.iter(f"{_XLSX_MAIN}sheet")
                if sheet.get("name") == sheet_name
            ),
            None,
        )
        if rel_id is None:
            raise ValueError(f"Không tìm thấy sheet {sheet_name!r} trong {path.name}")
        target = targets[rel_id].lstrip("/")
        if not target.startswith("xl/"):
            target = f"xl/{target}"
        sheet_root = ET.fromstring(book.read(target))

    for row in sheet_root.iter(f"{_XLSX_MAIN}row"):
        cells: dict[str, str] = {}
        for cell in row.findall(f"{_XLSX_MAIN}c"):
            column = "".join(ch for ch in cell.get("r", "") if ch.isalpha())
            cell_type = cell.get("t")
            if cell_type == "inlineStr":
                text = "".join(node.text or "" for node in cell.iter(f"{_XLSX_MAIN}t"))
            else:
                value = cell.find(f"{_XLSX_MAIN}v")
                text = (value.text or "") if value is not None else ""
                if cell_type == "s" and text:
                    text = shared[int(text)]
            cells[column] = text
        yield cells


def _normalize_guide_code(text: str) -> str:
    text = text.strip()
    return text[:-2] if text.endswith(".0") and text[:-2].lstrip("-").isdigit() else text


class CodeLabels:
    """Tra nhãn theo (bảng nguồn, cột, mã) từ sheet 2024_code_list của DfT."""

    def __init__(self, labels: dict[tuple[str, str, str], str]) -> None:
        self._labels = labels

    @classmethod
    def from_guide(cls, path: Path) -> CodeLabels:
        if not path.exists():
            raise SystemExit(
                f"Thiếu bảng tra mã {path}. Tải 'Open dataset data guide' từ "
                "https://www.gov.uk/government/statistical-data-sets/road-safety-open-data"
            )
        labels: dict[tuple[str, str, str], str] = {}
        for cells in read_xlsx_rows(path, GUIDE_SHEET):
            table, field, code, label = (cells.get(col, "").strip() for col in "ABCD")
            if table and field and code and label and table != "table":
                labels[(table, field, _normalize_guide_code(code))] = label
        log.info("Đọc %s nhãn mã từ %s", f"{len(labels):,}", path.name)
        return cls(labels)

    def label(self, table: str, field: str, code: int | str) -> str:
        text = self._labels.get((table, field, str(code)))
        if text:
            return text
        if code in (UNKNOWN_CODE, UNKNOWN_TEXT):
            return UNKNOWN_LABEL
        return f"Code {code} (not in data guide)"

    def coded(self, table: str, row: dict[str, str], field: str) -> tuple[int, str]:
        code = parse_code(row.get(field))
        return code, self.label(table, field, code)

    def text_coded(self, table: str, row: dict[str, str], field: str) -> tuple[str, str]:
        code = parse_text_code(row.get(field))
        return code, self.label(table, field, code)

    def flatten(self, table: str, row: dict[str, str], fields: Sequence[str]) -> tuple:
        values: list[int | str] = []
        for field in fields:
            values.extend(self.coded(table, row, field))
        return tuple(values)


# --------------------------------------------------------------------------- #
# Dimension và fact
# --------------------------------------------------------------------------- #
class Dimension:
    """Gán surrogate key cho mỗi tổ hợp thuộc tính khác nhau (khóa bắt đầu từ 1)."""

    def __init__(self, table: str, key: str, columns: Sequence[str]) -> None:
        self.table = table
        self.key = key
        self.columns = list(columns)
        self._keys: dict[tuple, int] = {}
        self.rows: list[tuple] = []

    def key_for(self, values: tuple) -> int:
        key = self._keys.get(values)
        if key is None:
            key = len(self._keys) + 1
            self._keys[values] = key
            self.rows.append((key, *values))
        return key

    def write(self, out_dir: Path) -> int:
        return write_table(out_dir, self.table, [self.key, *self.columns], self.rows)


class CollisionContext(NamedTuple):
    date_key: int
    time_key: int
    location_key: int
    road_key: int
    conditions_key: int
    severity_key: int
    number_of_vehicles: int
    number_of_casualties: int


class StarBuilder:
    """Transform: biến dòng nguồn thành dòng fact và dựng các dimension đi kèm."""

    def __init__(self, labels: CodeLabels) -> None:
        self.labels = labels
        self.location = Dimension("dim_location", "location_key", LOCATION_COLUMNS)
        self.road = Dimension("dim_road", "road_key", ROAD_COLUMNS)
        self.conditions = Dimension("dim_conditions", "conditions_key", CONDITION_COLUMNS)
        self.vehicle = Dimension("dim_vehicle", "vehicle_key", VEHICLE_COLUMNS)
        self.driver = Dimension("dim_driver", "driver_key", DRIVER_COLUMNS)
        self.action = Dimension("dim_vehicle_action", "action_key", ACTION_COLUMNS)
        self.casualty = Dimension("dim_casualty", "casualty_profile_key", CASUALTY_COLUMNS)
        self.collisions: dict[str, CollisionContext] = {}
        self.vehicle_keys: dict[str, int] = {}
        self.first_date: date | None = None
        self.last_date: date | None = None
        self.stats: Counter[str] = Counter()

    def collision_facts(
        self, rows: Iterable[dict[str, str]], years: set[str], limit: int | None
    ) -> Iterator[tuple]:
        labels = self.labels
        for raw in rows:
            self.stats["collision_read"] += 1
            if years and raw["collision_year"].strip() not in years:
                self.stats["collision_filtered_by_year"] += 1
                continue
            if limit and len(self.collisions) >= limit:
                break
            index = raw["collision_index"].strip()
            if not index or index in self.collisions:
                self.stats["collision_rejected_key"] += 1
                continue
            try:
                event_date = datetime.strptime(raw["date"].strip(), "%d/%m/%Y").date()
            except ValueError:
                self.stats["collision_rejected_date"] += 1
                log.warning("Bỏ vụ %s: ngày không hợp lệ %r", index, raw["date"])
                continue
            severity = parse_code(raw["collision_severity"])
            if severity not in SEVERITY_CODES:
                self.stats["collision_rejected_severity"] += 1
                continue

            location_key = self.location.key_for((
                *labels.coded("collision", raw, "police_force"),
                *labels.text_coded("collision", raw, "local_authority_ons_district"),
                *labels.text_coded("collision", raw, "local_authority_highway"),
                parse_text_code(raw["lsoa_of_accident_location"]),
                *labels.coded("collision", raw, "urban_or_rural_area"),
            ))
            road_key = self.road.key_for(
                labels.flatten("collision", raw, ROAD_FIELDS) + (parse_code(raw["speed_limit"]),)
            )
            conditions_key = self.conditions.key_for(
                labels.flatten("collision", raw, CONDITION_FIELDS)
            )
            context = CollisionContext(
                date_key=date_key(event_date),
                time_key=parse_time_key(raw["time"]),
                location_key=location_key,
                road_key=road_key,
                conditions_key=conditions_key,
                severity_key=severity,
                number_of_vehicles=parse_measure(raw["number_of_vehicles"]) or 0,
                number_of_casualties=parse_measure(raw["number_of_casualties"]) or 0,
            )
            self.collisions[index] = context
            self.first_date = min(self.first_date or event_date, event_date)
            self.last_date = max(self.last_date or event_date, event_date)
            self.stats["collision_loaded"] += 1
            yield (
                len(self.collisions),
                index,
                context.date_key,
                context.time_key,
                location_key,
                road_key,
                conditions_key,
                severity,
                context.number_of_vehicles,
                context.number_of_casualties,
                *severity_flags(severity),
                parse_decimal_text(raw["collision_adjusted_severity_serious"]),
                parse_decimal_text(raw["collision_adjusted_severity_slight"]),
                int(parse_code(raw["collision_injury_based"]) == 1),
                int(parse_code(raw["did_police_officer_attend_scene_of_accident"]) == 1),
                parse_decimal_text(raw["longitude"]),
                parse_decimal_text(raw["latitude"]),
            )

    def vehicle_facts(self, rows: Iterable[dict[str, str]]) -> Iterator[tuple]:
        labels = self.labels
        fact_key = 0
        for raw in rows:
            self.stats["vehicle_read"] += 1
            index = raw["collision_index"].strip()
            context = self.collisions.get(index)
            if context is None:
                self.stats["vehicle_skipped_collision_not_loaded"] += 1
                continue
            reference = parse_code(raw["vehicle_reference"])
            engine_cc = parse_measure(raw["engine_capacity_cc"])
            vehicle_age = parse_measure(raw["age_of_vehicle"])
            vehicle_key = self.vehicle.key_for(
                labels.flatten("vehicle", raw, VEHICLE_FIELDS)
                + (engine_capacity_band(engine_cc), vehicle_age_band(vehicle_age))
            )
            driver_key = self.driver.key_for(labels.flatten("vehicle", raw, DRIVER_FIELDS))
            action_key = self.action.key_for(labels.flatten("vehicle", raw, ACTION_FIELDS))
            self.vehicle_keys[f"{index}|{reference}"] = vehicle_key
            fact_key += 1
            self.stats["vehicle_loaded"] += 1
            yield (
                fact_key,
                index,
                reference,
                context.date_key,
                context.time_key,
                context.location_key,
                context.road_key,
                context.conditions_key,
                context.severity_key,
                vehicle_key,
                driver_key,
                action_key,
                1,
                parse_measure(raw["age_of_driver"]),
                engine_cc,
                vehicle_age,
            )

    def casualty_facts(self, rows: Iterable[dict[str, str]]) -> Iterator[tuple]:
        labels = self.labels
        fact_key = 0
        for raw in rows:
            self.stats["casualty_read"] += 1
            index = raw["collision_index"].strip()
            context = self.collisions.get(index)
            if context is None:
                self.stats["casualty_skipped_collision_not_loaded"] += 1
                continue
            severity = parse_code(raw["casualty_severity"])
            if severity not in SEVERITY_CODES:
                self.stats["casualty_rejected_severity"] += 1
                continue
            reference = parse_code(raw["vehicle_reference"])
            vehicle_key = self.vehicle_keys.get(f"{index}|{reference}")
            if vehicle_key is None:
                self.stats["casualty_without_vehicle"] += 1
            casualty_key = self.casualty.key_for(
                labels.flatten("casualty", raw, CASUALTY_FIELDS)
            )
            fact_key += 1
            self.stats["casualty_loaded"] += 1
            yield (
                fact_key,
                index,
                reference,
                parse_code(raw["casualty_reference"]),
                context.date_key,
                context.time_key,
                context.location_key,
                context.road_key,
                context.conditions_key,
                severity,
                casualty_key,
                vehicle_key,
                1,
                *severity_flags(severity),
                parse_decimal_text(raw["casualty_adjusted_severity_serious"]),
                parse_decimal_text(raw["casualty_adjusted_severity_slight"]),
                parse_measure(raw["age_of_casualty"]),
            )

    def date_rows(self) -> Iterator[tuple]:
        """Lịch liên tục từ ngày đầu tới ngày cuối, kể cả ngày không có vụ nào."""
        if self.first_date is None or self.last_date is None:
            return
        day = self.first_date
        while day <= self.last_date:
            iso_year, iso_week, iso_weekday = day.isocalendar()
            yield (
                date_key(day),
                day.isoformat(),
                day.day,
                iso_weekday,
                DAY_NAMES[day.weekday()],
                int(day.weekday() >= 5),
                iso_week,
                day.month,
                MONTH_NAMES[day.month - 1],
                (day.month - 1) // 3 + 1,
                day.year,
            )
            day += timedelta(days=1)

    @staticmethod
    def time_rows() -> Iterator[tuple]:
        yield (UNKNOWN_CODE, None, None, "Unknown", 0)
        for hour in range(24):
            band = next(label for start, end, label in TIME_BANDS if start <= hour <= end)
            for minute in range(60):
                yield (hour * 100 + minute, hour, minute, band, int(band in PEAK_BANDS))

    def severity_rows(self) -> list[tuple]:
        return [
            (code, self.labels.label("collision", "collision_severity", code))
            for code in SEVERITY_CODES
        ]

    def write_dimensions(self, out_dir: Path) -> None:
        write_table(out_dir, "dim_date", DATE_COLUMNS, self.date_rows())
        write_table(out_dir, "dim_time", TIME_COLUMNS, self.time_rows())
        write_table(out_dir, "dim_severity", SEVERITY_COLUMNS, self.severity_rows())
        for dimension in (
            self.location, self.road, self.conditions,
            self.vehicle, self.driver, self.action, self.casualty,
        ):
            dimension.write(out_dir)

    def reconciliation(self) -> list[tuple[str, int]]:
        """Đối soát: số xe / nạn nhân khai trong bảng va chạm so với số dòng đã nạp."""
        expected_vehicles = sum(c.number_of_vehicles for c in self.collisions.values())
        expected_casualties = sum(c.number_of_casualties for c in self.collisions.values())
        checks = (
            ("vehicle", expected_vehicles, self.stats["vehicle_loaded"]),
            ("casualty", expected_casualties, self.stats["casualty_loaded"]),
        )
        for name, expected, loaded in checks:
            if expected == loaded:
                log.info("Đối soát %s: khớp %s dòng", name, f"{loaded:,}")
            else:
                log.warning(
                    "Đối soát %s: bảng va chạm khai %s, đã nạp %s",
                    name, f"{expected:,}", f"{loaded:,}",
                )
        metrics = sorted(self.stats.items())
        metrics.append(("vehicle_expected_from_collisions", expected_vehicles))
        metrics.append(("casualty_expected_from_collisions", expected_casualties))
        return metrics


# --------------------------------------------------------------------------- #
# Extract / Load
# --------------------------------------------------------------------------- #
def extract(path: Path) -> Iterator[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Thiếu file nguồn {path}")
    log.info("Extract %s", path.name)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def write_table(
    out_dir: Path, table: str, columns: Sequence[str], rows: Iterable[Sequence]
) -> int:
    path = out_dir / f"{table}.csv"
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(row)
            count += 1
    log.info("Ghi %s: %s dòng", path.name, f"{count:,}")
    return count


def load_postgres(out_dir: Path, database_url: str) -> None:
    """Xóa dữ liệu cũ rồi COPY toàn bộ CSV vào dw.* trong một transaction."""
    try:
        import psycopg
    except ImportError as exc:
        raise SystemExit('Cần psycopg để nạp CSDL: pip install "psycopg[binary]"') from exc

    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE " + ", ".join(f"dw.{table}" for table in LOAD_ORDER))
        for table in LOAD_ORDER:
            path = out_dir / f"{table}.csv"
            with path.open(encoding="utf-8", newline="") as handle:
                columns = ", ".join(next(csv.reader(handle)))
            statement = (
                f"COPY dw.{table} ({columns}) FROM STDIN "
                "WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')"
            )
            with path.open("rb") as handle, cur.copy(statement) as copy:
                while chunk := handle.read(1 << 20):
                    copy.write(chunk)
            log.info("Nạp dw.%s", table)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ETL STATS19 -> kho dữ liệu dw")
    parser.add_argument("--years", nargs="+", help="chỉ nạp các năm này, ví dụ --years 2024 2025")
    parser.add_argument("--limit", type=int, help="chỉ nạp N vụ đầu tiên cùng xe và nạn nhân của chúng")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR, help="thư mục dữ liệu nguồn")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR, help="thư mục ghi CSV đã xử lý")
    parser.add_argument(
        "--load", action="store_true",
        help="sau khi ghi CSV, COPY vào PostgreSQL theo biến môi trường DW_DATABASE_URL",
    )
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> None:
    labels = CodeLabels.from_guide(args.raw_dir / GUIDE_FILE)
    builder = StarBuilder(labels)
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    years = {year.strip() for year in args.years or []}

    write_table(
        out_dir, "fact_collision", FACT_COLLISION_COLUMNS,
        builder.collision_facts(extract(args.raw_dir / COLLISION_FILE), years, args.limit),
    )
    if not builder.collisions:
        raise SystemExit("Không nạp được vụ va chạm nào. Kiểm tra --years hoặc file nguồn.")
    write_table(
        out_dir, "fact_vehicle", FACT_VEHICLE_COLUMNS,
        builder.vehicle_facts(extract(args.raw_dir / VEHICLE_FILE)),
    )
    write_table(
        out_dir, "fact_casualty", FACT_CASUALTY_COLUMNS,
        builder.casualty_facts(extract(args.raw_dir / CASUALTY_FILE)),
    )
    builder.write_dimensions(out_dir)
    write_table(out_dir, "etl_report", ["metric", "value"], builder.reconciliation())

    if args.load:
        database_url = os.environ.get("DW_DATABASE_URL")
        if not database_url:
            raise SystemExit("Đặt biến môi trường DW_DATABASE_URL trước khi dùng --load.")
        load_postgres(out_dir, database_url)


if __name__ == "__main__":
    run(parse_args())
