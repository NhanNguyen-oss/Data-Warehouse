"""
Danh mục nguồn dữ liệu, tải nguồn còn thiếu và lập source manifest có checksum.

Raw là bất biến: script chỉ tải file chưa có, không ghi đè file đã tồn tại.
Manifest (data/manifest/source_manifest.json) được commit để người khác kiểm tra
mình đang dùng đúng bản phát hành; bản thân file dữ liệu lớn không commit.

Cách chạy (chỉ cần thư viện chuẩn):
    python src/etl/sources.py list                 liệt kê nguồn và trạng thái trên máy
    python src/etl/sources.py fetch                tải các nguồn DfT Traffic còn thiếu
    python src/etl/sources.py manifest             tính sha256, kích thước, số dòng -> manifest
    python src/etl/sources.py verify               so file trên máy với manifest đã commit
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import logging
import sys
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure is not None:
        _reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
MANIFEST_PATH = ROOT / "data" / "manifest" / "source_manifest.json"

ROAD_SAFETY_PAGE = "https://www.gov.uk/government/statistical-data-sets/road-safety-open-data"
TRAFFIC_PAGE = "https://roadtraffic.dft.gov.uk/downloads"
TRAFFIC_BASE = "https://storage.googleapis.com/dft-statistics/road-traffic/downloads/data-gov-uk"
LICENCE = "Open Government Licence v3.0"

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("sources")


@dataclass(frozen=True)
class Source:
    source_id: str
    relative_path: str
    role: str
    publisher_page: str
    download_url: str | None = None

    @property
    def path(self) -> Path:
        return RAW_DIR / self.relative_path


SOURCES: tuple[Source, ...] = (
    Source(
        "stats19_collision",
        "dft-road-casualty-statistics-collision-last-5-years.csv",
        "STATS19 collision events, một dòng = một vụ",
        ROAD_SAFETY_PAGE,
    ),
    Source(
        "stats19_vehicle",
        "dft-road-casualty-statistics-vehicle-last-5-years.csv",
        "STATS19 vehicles, một dòng = một xe trong một vụ",
        ROAD_SAFETY_PAGE,
    ),
    Source(
        "stats19_casualty",
        "dft-road-casualty-statistics-casualty-last-5-years.csv",
        "STATS19 casualties, một dòng = một nạn nhân",
        ROAD_SAFETY_PAGE,
    ),
    Source(
        "stats19_data_guide",
        "dft-road-casualty-statistics-road-safety-open-dataset-data-guide-2025.xlsx",
        "Codebook STATS19 (mã -> nhãn)",
        ROAD_SAFETY_PAGE,
    ),
    Source(
        "traffic_aadf",
        "traffic/dft_traffic_counts_aadf.zip",
        "AADF theo count point x year",
        TRAFFIC_PAGE,
        f"{TRAFFIC_BASE}/dft_traffic_counts_aadf.zip",
    ),
    Source(
        "traffic_count_points",
        "traffic/count_points.zip",
        "Metadata count points",
        TRAFFIC_PAGE,
        f"{TRAFFIC_BASE}/count_points.zip",
    ),
    Source(
        "traffic_local_authority",
        "traffic/local_authority_traffic.csv",
        "Vehicle miles ước tính theo local authority x year (toàn mạng đường)",
        TRAFFIC_PAGE,
        f"{TRAFFIC_BASE}/local_authority_traffic.csv",
    ),
)


def source_by_id(source_id: str) -> Source:
    for source in SOURCES:
        if source.source_id == source_id:
            return source
    raise KeyError(source_id)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def count_csv_rows(handle: io.TextIOBase) -> tuple[int, list[str]]:
    """Số bản ghi (không tính header) theo CSV parser, không theo số dòng vật lý."""
    reader = csv.reader(handle)
    header = next(reader, [])
    return sum(1 for _ in reader), header


def describe_members(path: Path) -> list[dict]:
    """Mô tả từng CSV trong file (zip có thể chứa nhiều member)."""
    if path.suffix == ".zip":
        members = []
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if not info.filename.lower().endswith(".csv"):
                    continue
                with archive.open(info) as raw:
                    rows, header = count_csv_rows(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
                members.append({
                    "name": info.filename,
                    "uncompressed_bytes": info.file_size,
                    "archive_timestamp": datetime(*info.date_time).isoformat(),
                    "rows": rows,
                    "columns": len(header),
                })
        return members
    if path.suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows, header = count_csv_rows(handle)
        return [{"name": path.name, "rows": rows, "columns": len(header)}]
    return []


def manifest_entry(source: Source) -> dict:
    path = source.path
    entry = {
        "source_id": source.source_id,
        "path": f"data/raw/{source.relative_path}",
        "role": source.role,
        "publisher_page": source.publisher_page,
        "download_url": source.download_url,
        "licence": LICENCE,
        "present": path.exists(),
    }
    if path.exists():
        entry.update({
            "bytes": path.stat().st_size,
            "sha256": sha256_of(path),
            "members": describe_members(path),
        })
    return entry


def build_manifest(sources: Sequence[Source] = SOURCES) -> dict:
    return {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "generator": "src/etl/sources.py manifest",
        "sources": [manifest_entry(source) for source in sources],
    }


def fetch(source: Source, timeout: int = 600) -> bool:
    """Tải nguồn nếu chưa có. Trả True nếu vừa tải."""
    if source.path.exists():
        log.info("Đã có %s, bỏ qua (raw bất biến)", source.relative_path)
        return False
    if not source.download_url:
        log.warning("%s không có link tải trực tiếp; tải tay từ %s", source.relative_path, source.publisher_page)
        return False
    source.path.parent.mkdir(parents=True, exist_ok=True)
    partial = source.path.with_name(source.path.name + ".part")
    log.info("Tải %s", source.download_url)
    with urllib.request.urlopen(source.download_url, timeout=timeout) as response, partial.open("wb") as out:
        while chunk := response.read(1 << 20):
            out.write(chunk)
    partial.replace(source.path)
    log.info("Đã lưu %s (%s bytes)", source.relative_path, f"{source.path.stat().st_size:,}")
    return True


def verify(manifest_path: Path = MANIFEST_PATH) -> list[str]:
    """Trả danh sách khác biệt giữa file trên máy và manifest đã commit."""
    recorded = json.loads(manifest_path.read_text(encoding="utf-8"))
    problems = []
    for entry in recorded["sources"]:
        if not entry.get("sha256"):
            continue
        path = ROOT / entry["path"]
        if not path.exists():
            problems.append(f"{entry['path']}: thiếu trên máy")
        elif sha256_of(path) != entry["sha256"]:
            problems.append(f"{entry['path']}: sha256 khác manifest (bản phát hành khác?)")
    return problems


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Danh mục, tải và manifest nguồn dữ liệu")
    parser.add_argument("command", choices=("list", "fetch", "manifest", "verify"))
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "list":
        for source in SOURCES:
            status = "có" if source.path.exists() else "THIẾU"
            print(f"{status:5} {source.source_id:26} data/raw/{source.relative_path}")
    elif args.command == "fetch":
        for source in SOURCES:
            fetch(source)
    elif args.command == "manifest":
        manifest = build_manifest()
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        log.info("Ghi %s", args.manifest.relative_to(ROOT) if args.manifest.is_relative_to(ROOT) else args.manifest)
    elif args.command == "verify":
        problems = verify(args.manifest)
        for problem in problems:
            log.error(problem)
        if problems:
            return 1
        log.info("Mọi file có trong manifest đều khớp sha256")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
