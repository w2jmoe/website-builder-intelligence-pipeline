#!/usr/bin/env python3
"""竞品监控：历史快照保存与变更检测。"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
HISTORY_DIR = BASE_DIR / "data" / "history"
CHANGE_REPORT_PATH = BASE_DIR / "data" / "change_report.json"

TRACKED_FIELDS = (
    "pricing",
    "core_features",
    "target_customer",
    "technical_highlights",
)

logger = logging.getLogger(__name__)


def _normalize_field(field: str, value: Any) -> Any:
    if field in ("core_features", "technical_highlights"):
        return sorted(str(v).strip().lower() for v in (value or []))
    return str(value or "").strip()


def _load_snapshot(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"快照格式错误: {path}")
    return data


def _index_by_name(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {r.get("name", ""): r for r in records if r.get("name")}


def _list_snapshots(history_dir: Path = HISTORY_DIR) -> list[Path]:
    if not history_dir.exists():
        return []
    return sorted(history_dir.glob("????-??-??.json"), reverse=True)


def save_snapshot(
    records: list[dict[str, Any]],
    history_dir: Path = HISTORY_DIR,
    snapshot_date: date | None = None,
) -> Path:
    """保存带日期的历史快照。"""
    history_dir.mkdir(parents=True, exist_ok=True)
    date_str = (snapshot_date or date.today()).strftime("%Y-%m-%d")
    path = history_dir / f"{date_str}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    logger.info("历史快照已保存 -> %s", path)
    return path


def _detect_changes(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> list[str]:
    changed: list[str] = []
    for field in TRACKED_FIELDS:
        old_val = _normalize_field(field, previous.get(field))
        new_val = _normalize_field(field, current.get(field))
        if old_val != new_val:
            changed.append(field)
    return changed


def _format_change_message(name: str, changed_fields: list[str]) -> str:
    parts = [f"{field} updated" for field in changed_fields]
    return f"{name} {', '.join(parts)}"


def compare_snapshots(
    previous_records: list[dict[str, Any]],
    current_records: list[dict[str, Any]],
    previous_date: str,
    current_date: str,
) -> dict[str, Any]:
    """比较两次快照，返回变更报告结构。"""
    prev_map = _index_by_name(previous_records)
    curr_map = _index_by_name(current_records)
    all_names = list(dict.fromkeys(list(prev_map) + list(curr_map)))

    competitors_report: list[dict[str, Any]] = []
    for name in all_names:
        prev = prev_map.get(name, {})
        curr = curr_map.get(name, {})
        changed_fields = _detect_changes(prev, curr)
        entry: dict[str, Any] = {"name": name}
        if changed_fields:
            entry["status"] = "changed"
            entry["changes"] = changed_fields
        else:
            entry["status"] = "unchanged"
        competitors_report.append(entry)

    return {
        "compared_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "previous_snapshot": previous_date,
        "current_snapshot": current_date,
        "competitors": competitors_report,
    }


def _print_change_logs(report: dict[str, Any]) -> None:
    changed_lines: list[str] = []
    unchanged_lines: list[str] = []

    for entry in report.get("competitors", []):
        name = entry.get("name", "")
        if entry.get("status") == "changed":
            changed_lines.append(_format_change_message(name, entry.get("changes", [])))
        else:
            unchanged_lines.append(name)

    if changed_lines:
        print("[CHANGED]")
        for line in changed_lines:
            print(line)
        print()

    if unchanged_lines:
        print("[UNCHANGED]")
        for name in unchanged_lines:
            print(name)


def run_competitor_monitor(
    records: list[dict[str, Any]],
    history_dir: Path = HISTORY_DIR,
    change_report_path: Path = CHANGE_REPORT_PATH,
) -> dict[str, Any] | None:
    """
    保存今日快照，并与上一期快照比较。
    历史数据不足时跳过比较。
    """
    save_snapshot(records, history_dir)

    snapshots = _list_snapshots(history_dir)
    if len(snapshots) < 2:
        logger.info("历史快照不足（需至少 2 次运行），跳过变更比较")
        return None

    current_path, previous_path = snapshots[0], snapshots[1]
    current_date = current_path.stem
    previous_date = previous_path.stem

    try:
        current_records = _load_snapshot(current_path)
        previous_records = _load_snapshot(previous_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        logger.error("读取快照失败，跳过变更比较: %s", exc)
        return None

    report = compare_snapshots(
        previous_records,
        current_records,
        previous_date,
        current_date,
    )

    change_report_path.parent.mkdir(parents=True, exist_ok=True)
    with change_report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info("变更报告已写入 -> %s", change_report_path)
    _print_change_logs(report)
    return report
