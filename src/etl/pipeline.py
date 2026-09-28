"""
CO4031 | Khung quy trình ETL: Extract -> Transform -> Load.

Chạy thử với dữ liệu demo (không cần CSDL):
    python src/etl/pipeline.py

Khi đã có file nguồn, đặt CSV tại data/raw/source.csv rồi chạy lại.
Cột tối thiểu của file nguồn: txn_id, txn_date, entity_id, entity_name, amount, quantity.

Việc nhóm phải thay:
    - extract(): đọc đúng nguồn (CSV, API, CSDL tác nghiệp).
    - transform(): quy tắc làm sạch và chuẩn hóa theo đề tài.
    - load(): ghi vào các bảng dw.* đã khai báo trong src/database/schema.sql.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure is not None:
        _reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
RAW_FILE = ROOT / "data" / "raw" / "source.csv"
OUT_DIR = ROOT / "data" / "processed"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("etl")


@dataclass(frozen=True)
class EventRow:
    """Một dòng đã sạch, sẵn sàng nạp vào fact và dimension."""

    source_txn_id: str
    date_key: int
    entity_id: str
    entity_name: str
    quantity: Decimal
    amount: Decimal


# Dữ liệu minh họa để pipeline chạy được trước khi nhóm có file nguồn.
DEMO_SOURCE = [
    {
        "txn_id": "T001",
        "txn_date": "2026-01-15",
        "entity_id": "E01",
        "entity_name": "Thuc the mau A",
        "amount": "120.50",
        "quantity": "2",
    },
    {
        "txn_id": "T002",
        "txn_date": "15/01/2026",
        "entity_id": "e01",
        "entity_name": "  Thuc the mau A  ",
        "amount": "80",
        "quantity": "1",
    },
    {
        "txn_id": "",
        "txn_date": "2026-02-01",
        "entity_id": "E02",
        "entity_name": "Thuc the mau B",
        "amount": "not-a-number",
        "quantity": "3",
    },
]


def extract() -> list[dict[str, str]]:
    """Đọc dữ liệu thô. Ưu tiên CSV trong data/raw/, không có thì dùng demo."""
    if RAW_FILE.exists():
        log.info("Extract từ file: %s", RAW_FILE)
        with RAW_FILE.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    log.info("Chưa có %s — dùng DEMO_SOURCE.", RAW_FILE)
    return list(DEMO_SOURCE)


def _parse_date(value: str) -> datetime:
    text = (value or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"Không đọc được ngày: {value!r}")


def _parse_decimal(value: str) -> Decimal:
    try:
        return Decimal((value or "").strip().replace(",", ""))
    except InvalidOperation as exc:
        raise ValueError(f"Không đọc được số: {value!r}") from exc


def transform(raw_rows: list[dict[str, str]]) -> list[EventRow]:
    """Làm sạch: chuẩn hóa khóa, kiểu dữ liệu, loại bản ghi lỗi."""
    clean: list[EventRow] = []
    rejected = 0
    for index, row in enumerate(raw_rows, start=1):
        try:
            txn_id = (row.get("txn_id") or "").strip()
            entity_id = (row.get("entity_id") or "").strip().upper()
            entity_name = " ".join((row.get("entity_name") or "").split())
            if not txn_id or not entity_id or not entity_name:
                raise ValueError("Thiếu khóa nghiệp vụ")
            event_date = _parse_date(row.get("txn_date", ""))
            clean.append(
                EventRow(
                    source_txn_id=txn_id,
                    date_key=int(event_date.strftime("%Y%m%d")),
                    entity_id=entity_id,
                    entity_name=entity_name,
                    quantity=_parse_decimal(row.get("quantity", "")),
                    amount=_parse_decimal(row.get("amount", "")),
                )
            )
        except ValueError as exc:
            rejected += 1
            log.warning("Bỏ dòng %s: %s", index, exc)
    log.info("Transform: %s dòng hợp lệ, %s dòng bị loại.", len(clean), rejected)
    return clean


def load(rows: list[EventRow]) -> Path:
    """
    Bản khung ghi CSV đã xử lý.

    TODO: thay hàm này bằng INSERT vào dw.dim_date, dw.dim_entity, dw.fact_event.
    Gợi ý: sqlalchemy hoặc psycopg, chạy trong một transaction.
    SCD Type 2: so business key + thuộc tính; nếu đổi thì đóng phiên bản cũ.
    """
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUT_DIR / "fact_event.csv"
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "source_txn_id",
                "date_key",
                "entity_id",
                "entity_name",
                "quantity",
                "amount",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "source_txn_id": row.source_txn_id,
                    "date_key": row.date_key,
                    "entity_id": row.entity_id,
                    "entity_name": row.entity_name,
                    "quantity": str(row.quantity),
                    "amount": str(row.amount),
                }
            )
    log.info("Load xong %s dòng vào %s", len(rows), target)
    return target


def run() -> None:
    raw_rows = extract()
    clean_rows = transform(raw_rows)
    load(clean_rows)


if __name__ == "__main__":
    run()
