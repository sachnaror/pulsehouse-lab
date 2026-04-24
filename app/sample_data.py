from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import random


@dataclass
class LogEvent:
    ts: datetime
    endpoint: str
    method: str
    status: int
    duration_ms: float
    region: str
    service: str
    bytes_sent: int
    error_code: str


ENDPOINTS = [
    "/api/orders",
    "/api/orders/{id}",
    "/api/payments",
    "/api/menu",
    "/api/cart",
    "/api/search",
    "/api/login",
]

METHODS = ["GET", "POST", "PUT"]
REGIONS = ["ap-south", "us-east", "eu-west"]
SERVICES = ["checkout", "catalog", "gateway", "search"]
ERROR_CODES = ["", "", "", "", "TIMEOUT", "DB_LOCK", "UPSTREAM_502", "INVALID_TOKEN"]


def generate_events(count: int = 2400) -> list[dict]:
    random.seed(42)
    now = datetime.utcnow()
    events: list[dict] = []

    for index in range(count):
        ts = now - timedelta(minutes=(count - index) * 2)
        endpoint = random.choice(ENDPOINTS)
        method = random.choice(METHODS)
        service = random.choice(SERVICES)
        region = random.choice(REGIONS)

        base_status = 200
        duration = random.gauss(180, 55)
        error_code = ""

        if endpoint == "/api/payments" and ts.hour in {10, 11, 18} and random.random() < 0.18:
            base_status = random.choice([500, 502, 504])
            duration += random.randint(350, 900)
            error_code = random.choice(["TIMEOUT", "UPSTREAM_502"])
        elif random.random() < 0.08:
            base_status = random.choice([401, 404, 429, 500])
            duration += random.randint(50, 300)
            error_code = random.choice(ERROR_CODES)

        if service == "search":
            duration += random.randint(30, 120)
        if service == "catalog":
            duration -= random.randint(5, 25)

        event = LogEvent(
            ts=ts,
            endpoint=endpoint,
            method=method,
            status=base_status,
            duration_ms=max(18.0, round(duration, 2)),
            region=region,
            service=service,
            bytes_sent=random.randint(500, 9000),
            error_code=error_code,
        )
        events.append(asdict(event))

    return events
