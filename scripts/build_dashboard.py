#!/usr/bin/env python3
"""Build a self-contained category-sales trend dashboard from verified MCP data.

The input is JSON from the analysis workflow. This utility deliberately accepts
only already-confirmed monthly figures; it does not call SellerSprite or invent
missing values.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
CURRENCY_BY_MARKETPLACE = {
    "US": "USD", "UK": "GBP", "AU": "AUD", "CA": "CAD", "JP": "JPY",
    "DE": "EUR", "FR": "EUR", "IT": "EUR", "ES": "EUR", "MX": "MXN",
    "BR": "BRL", "IN": "INR", "AE": "AED",
}


def fail(message: str) -> None:
    raise ValueError(message)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_month(value: Any, name: str) -> str:
    if not isinstance(value, str) or not MONTH_RE.fullmatch(value):
        fail(f"{name} 必须为 YYYY-MM。")
    return value


def shift_month(month: str, offset: int) -> str:
    year, mon = (int(part) for part in month.split("-"))
    index = year * 12 + mon - 1 + offset
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def number_or_none(value: Any, field: str, month: str) -> float | int | None:
    if value is None:
        return None
    if not is_number(value) or value < 0:
        fail(f"{month} 的 {field} 必须是非负数或 null。")
    return value


def normalize_rows(source: Any, cutoff: str, blocked: bool) -> list[dict[str, Any]]:
    if not isinstance(source, list):
        fail("monthly 必须是数组。")
    if blocked and not source:
        return []
    if len(source) != 24:
        fail("非阻断状态必须恰好提供截至目标月份的 24 个自然月。")

    expected = [shift_month(cutoff, -23 + index) for index in range(24)]
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(source):
        if not isinstance(raw, dict):
            fail(f"monthly[{index}] 必须是对象。")
        month = validate_month(raw.get("month"), f"monthly[{index}].month")
        if month != expected[index]:
            fail(f"monthly[{index}] 应为 {expected[index]}，实际为 {month}。")
        row = {
            "month": month,
            "period": "前12个月" if index < 12 else "近12个月",
            "totalUnits": number_or_none(raw.get("totalUnits"), "totalUnits", month),
            "avgUnits": number_or_none(raw.get("avgUnits"), "avgUnits", month),
            "avgRevenue": number_or_none(raw.get("avgRevenue"), "avgRevenue", month),
            "avgPrice": number_or_none(raw.get("avgPrice"), "avgPrice", month),
            "totalProducts": number_or_none(raw.get("totalProducts"), "totalProducts", month),
        }
        if row["totalUnits"] is None:
            row["dataStatus"] = "missing"
            row["missingReason"] = str(raw.get("missingReason") or "该月份完整类目销量不可用")
        else:
            row["dataStatus"] = "available"
        rows.append(row)
    return rows


def total_and_coverage(rows: list[dict[str, Any]]) -> tuple[float | int | None, int]:
    values = [row["totalUnits"] for row in rows if is_number(row.get("totalUnits"))]
    return (sum(values) if values else None, len(values))


def format_number(value: float | int | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.0f}"


def kpi(label: str, value: float | int | None, signed: bool = False) -> dict[str, Any]:
    return {"label": label, "value": value, "signed": signed}


def normalize_category(source: Any, default_leaf_status: str) -> dict[str, str]:
    if not isinstance(source, dict):
        source = {}
    return {
        "englishPath": str(source.get("englishPath") or "—"),
        "localPath": str(source.get("localPath") or "—"),
        "nodeIdPath": str(source.get("nodeIdPath") or "—"),
        "leafStatus": str(source.get("leafStatus") or default_leaf_status),
    }


def build_payload(source: dict[str, Any]) -> dict[str, Any]:
    marketplace = source.get("marketplace")
    if not isinstance(marketplace, str) or marketplace.upper() not in CURRENCY_BY_MARKETPLACE:
        fail("marketplace 必须是受支持的站点代码。")
    marketplace = marketplace.upper()
    cutoff = validate_month(source.get("targetCutoffMonth"), "targetCutoffMonth")
    requested_status = source.get("status")
    if requested_status not in (None, "ready", "partial", "blocked"):
        fail("status 只能是 ready、partial 或 blocked。")
    blocked = requested_status == "blocked"
    rows = normalize_rows(source.get("monthly", []), cutoff, blocked)
    previous_total, previous_coverage = total_and_coverage(rows[:12])
    recent_total, recent_coverage = total_and_coverage(rows[12:])
    available_months = previous_coverage + recent_coverage

    if blocked:
        status = "blocked"
    elif available_months == 0:
        fail("没有任何可确认销量时，请使用 status=blocked 并说明 blockReason。")
    elif available_months == 24:
        status = "ready"
    else:
        status = "partial"

    comparison_complete = previous_coverage == 12 and recent_coverage == 12
    if comparison_complete and previous_total is not None and recent_total is not None:
        delta_value = recent_total - previous_total
        change_rate_value = None if previous_total == 0 else delta_value / previous_total * 100
        change_rate_display = "—" if change_rate_value is None else f"{change_rate_value:+.1f}%"
    else:
        delta_value = None
        change_rate_value = None
        change_rate_display = "—"

    known_rows = [row for row in rows if is_number(row.get("totalUnits"))]
    peak = max(known_rows, key=lambda row: row["totalUnits"], default=None)
    if peak:
        peak_text = f"{peak['month']}：{format_number(peak['totalUnits'])}"
    else:
        peak_text = "—"
    last_six = rows[-6:]
    if len(last_six) == 6 and all(is_number(row.get("totalUnits")) for row in last_six):
        prior_three = sum(row["totalUnits"] for row in last_six[:3])
        latest_three = sum(row["totalUnits"] for row in last_six[3:])
        recent_delta = latest_three - prior_three
        if prior_three == 0:
            recent_text = f"最近3个月合计 {format_number(latest_three)}；此前3个月为 0，未计算比例"
        else:
            recent_rate = recent_delta / prior_three * 100
            direction = "增加" if recent_delta > 0 else "减少" if recent_delta < 0 else "持平"
            recent_text = f"最近3个月较此前3个月{direction} {format_number(abs(recent_delta))}（{recent_rate:+.1f}%）"
    else:
        recent_text = "最近6个月覆盖不完整，未计算最近3个月表现"

    if comparison_complete and delta_value is not None:
        if delta_value > 0:
            overall = f"近12个月较前12个月增加 {format_number(delta_value)}（{change_rate_display}）"
        elif delta_value < 0:
            overall = f"近12个月较前12个月减少 {format_number(abs(delta_value))}（{change_rate_display}）"
        else:
            overall = "近12个月与前12个月销量持平（0.0%）"
    else:
        overall = "两个12个月周期的覆盖不完整，不计算同比变化"

    scope_label = f"完整类目月度销量（已确认 {available_months}/24 月）"
    output = {
        "status": status,
        "marketplace": marketplace,
        "productName": str(source.get("productName") or "—"),
        "targetCutoffMonth": cutoff,
        "currencyCode": str(source.get("currencyCode") or CURRENCY_BY_MARKETPLACE[marketplace]),
        "scopeLabel": scope_label,
        "category": normalize_category(source.get("category"), "未完成验证" if status == "blocked" else "已验证"),
        "coverage": {"expectedMonths": 24, "availableMonths": available_months},
        "monthly": rows,
        "kpis": {
            "previous": kpi(f"前12个月销量（{previous_coverage}/12月）", previous_total),
            "recent": kpi(f"近12个月销量（{recent_coverage}/12月）", recent_total),
            "delta": kpi("销量变化量", delta_value, signed=True),
            "changeRate": {"label": "销量变化比例", "value": change_rate_value, "display": change_rate_display},
        },
        "insights": {"overall": overall, "peak": peak_text, "recent": recent_text},
        "blockReason": str(source.get("blockReason") or "未能获取可用于分析的完整类目月度销量") if status == "blocked" else "",
        "generatedAt": source.get("generatedAt") or datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    return output


def load_json(path: str) -> dict[str, Any]:
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        fail("输入 JSON 的根节点必须是对象。")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a self-contained category-sales trend dashboard.")
    parser.add_argument("--data", required=True, help="Verified source JSON path, or - for standard input.")
    parser.add_argument("--output", required=True, help="Output HTML path.")
    parser.add_argument("--template", help="Optional dashboard HTML template path.")
    args = parser.parse_args()
    try:
        dashboard = build_payload(load_json(args.data))
        template_path = Path(args.template) if args.template else Path(__file__).parents[1] / "assets" / "category-sales-trend-template.html"
        template = template_path.read_text(encoding="utf-8")
        marker = "__DASHBOARD_DATA_JSON__"
        if template.count(marker) != 1:
            fail("模板必须且只能包含一个数据占位符。")
        serialized = json.dumps(dashboard, ensure_ascii=False, separators=(",", ":"))
        serialized = serialized.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
        result = template.replace(marker, serialized)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result, encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"构建失败：{error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
