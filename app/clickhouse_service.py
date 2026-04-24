from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
import os
from statistics import mean
from typing import Any

from .sample_data import generate_events

try:
    import clickhouse_connect
except ImportError:  # pragma: no cover - optional until deps are installed
    clickhouse_connect = None


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pulsehouse_logs
(
    ts DateTime,
    endpoint LowCardinality(String),
    method LowCardinality(String),
    status UInt16,
    duration_ms Float32,
    region LowCardinality(String),
    service LowCardinality(String),
    bytes_sent UInt32,
    error_code LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toDate(ts)
ORDER BY (service, endpoint, ts)
"""


class AnalyticsRepository:
    def __init__(self) -> None:
        self.sample_events = generate_events()
        self.client = self._create_client()

    def _create_client(self):
        if clickhouse_connect is None:
            return None

        host = os.getenv("CLICKHOUSE_HOST")
        if not host:
            return None

        try:
            return clickhouse_connect.get_client(
                host=host,
                port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
                username=os.getenv("CLICKHOUSE_USER", "default"),
                password=os.getenv("CLICKHOUSE_PASSWORD", ""),
                database=os.getenv("CLICKHOUSE_DATABASE", "default"),
            )
        except Exception:
            return None

    def ensure_seeded(self) -> dict[str, Any]:
        if not self.client:
            return {"mode": "sample", "rows": len(self.sample_events)}

        self.client.command(CREATE_TABLE_SQL)
        count = self.client.query("SELECT count() FROM pulsehouse_logs").first_row[0]
        if count == 0:
            self.client.insert("pulsehouse_logs", self._rows_for_clickhouse(), column_names=[
                "ts",
                "endpoint",
                "method",
                "status",
                "duration_ms",
                "region",
                "service",
                "bytes_sent",
                "error_code",
            ])
            count = self.client.query("SELECT count() FROM pulsehouse_logs").first_row[0]
        return {"mode": "clickhouse", "rows": count}

    def _rows_for_clickhouse(self) -> list[tuple]:
        rows = []
        for event in self.sample_events:
            rows.append(
                (
                    event["ts"],
                    event["endpoint"],
                    event["method"],
                    event["status"],
                    event["duration_ms"],
                    event["region"],
                    event["service"],
                    event["bytes_sent"],
                    event["error_code"],
                )
            )
        return rows

    def _events(self) -> list[dict[str, Any]]:
        if not self.client:
            return self.sample_events

        result = self.client.query(
            """
            SELECT ts, endpoint, method, status, duration_ms, region, service, bytes_sent, error_code
            FROM pulsehouse_logs
            ORDER BY ts
            """
        )
        return [
            {
                "ts": row[0],
                "endpoint": row[1],
                "method": row[2],
                "status": row[3],
                "duration_ms": float(row[4]),
                "region": row[5],
                "service": row[6],
                "bytes_sent": row[7],
                "error_code": row[8],
            }
            for row in result.result_rows
        ]

    def overview(self) -> dict[str, Any]:
        events = self._events()
        total_requests = len(events)
        errors = [event for event in events if event["status"] >= 500]
        avg_duration = mean(event["duration_ms"] for event in events)
        peak_minute = self._group_by_minute(events)
        busiest_bucket = max(peak_minute, key=lambda item: item["requests"])

        return {
            "mode": "clickhouse" if self.client else "sample",
            "total_requests": total_requests,
            "error_rate": round((len(errors) / total_requests) * 100, 2),
            "avg_duration_ms": round(avg_duration, 2),
            "peak_rpm": busiest_bucket["requests"],
            "peak_window": busiest_bucket["minute"],
        }

    def _group_by_minute(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"minute": "", "requests": 0, "errors": 0, "avg_duration": 0.0}
        )
        durations: dict[str, list[float]] = defaultdict(list)

        for event in events:
            minute = event["ts"].strftime("%H:%M")
            grouped[minute]["minute"] = minute
            grouped[minute]["requests"] += 1
            grouped[minute]["errors"] += int(event["status"] >= 500)
            durations[minute].append(event["duration_ms"])

        buckets = []
        for minute, payload in sorted(grouped.items()):
            payload["avg_duration"] = round(mean(durations[minute]), 2)
            buckets.append(payload)
        return buckets

    def timeseries(self) -> list[dict[str, Any]]:
        return self._group_by_minute(self._events())[-30:]

    def top_endpoints(self) -> list[dict[str, Any]]:
        events = self._events()
        counter = Counter(event["endpoint"] for event in events)
        duration_map: dict[str, list[float]] = defaultdict(list)
        error_map: dict[str, int] = defaultdict(int)

        for event in events:
            duration_map[event["endpoint"]].append(event["duration_ms"])
            error_map[event["endpoint"]] += int(event["status"] >= 500)

        rows = []
        for endpoint, total in counter.most_common(5):
            rows.append(
                {
                    "endpoint": endpoint,
                    "requests": total,
                    "avg_duration_ms": round(mean(duration_map[endpoint]), 2),
                    "server_errors": error_map[endpoint],
                }
            )
        return rows

    def anomalies(self) -> list[dict[str, Any]]:
        events = self._events()
        by_service: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in events:
            by_service[event["service"]].append(event)

        findings = []
        for service, rows in by_service.items():
            avg_latency = mean(row["duration_ms"] for row in rows)
            error_rate = sum(1 for row in rows if row["status"] >= 500) / len(rows)
            findings.append(
                {
                    "service": service,
                    "avg_latency_ms": round(avg_latency, 2),
                    "error_rate": round(error_rate * 100, 2),
                }
            )

        findings.sort(key=lambda row: (row["error_rate"], row["avg_latency_ms"]), reverse=True)
        return findings

    def explanation(self) -> str:
        anomalies = self.anomalies()
        top = anomalies[0]
        return (
            f"The largest spike is centered around the {top['service']} service. "
            f"It shows the highest error pressure and elevated latency, which usually points to a hot endpoint, "
            f"an upstream dependency issue, or a slow merge/write path if this were backed by a live event stream. "
            f"This is exactly the kind of pattern ClickHouse handles well because time-window aggregations stay fast "
            f"even as event volume grows."
        )
