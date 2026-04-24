# PulseHouse Lab

PulseHouse Lab is an experimental small FastAPI + Bootstrap demo that explains why ClickHouse is strong for observability and analytics workloads.

It gives you:

- a polished dashboard in the browser
- sample log ingestion
- KPIs, time-series charts, and top endpoints
- a restaurant analogy panel for ClickHouse vs MySQL/PostgreSQL/MongoDB/vector databases
- an optional real ClickHouse connection with a `MergeTree` schema

## Directory structure

```text
pulsehouse-lab/
├── .venv/
├── README.md
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── clickhouse_service.py
│   ├── sample_data.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── css/
│       │   └── styles.css
│       └── js/
│           └── dashboard.js
└── data/
```

## ClickHouse schema design

```sql
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
ORDER BY (service, endpoint, ts);
```

Why this schema works:

- `MergeTree` is the standard engine for analytics workloads.
- `PARTITION BY toDate(ts)` keeps time-based pruning efficient.
- `ORDER BY (service, endpoint, ts)` helps common filters on service, endpoint, and recent windows.
- `LowCardinality(String)` reduces storage for repeated labels like endpoint and region.

## Run locally

```bash
cd /Users/homesachin/Desktop/zoneone/practice/pulsehouse-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`

## Optional ClickHouse connection

Set these env vars before starting the app:

```bash
export CLICKHOUSE_HOST=localhost
export CLICKHOUSE_PORT=8123
export CLICKHOUSE_USER=default
export CLICKHOUSE_PASSWORD=
export CLICKHOUSE_DATABASE=default
```

If ClickHouse is not available, the app falls back to generated sample data so the browser demo still works.

## 📩 Contact

| Name              | Details                             |
|-------------------|-------------------------------------|
| **👨‍💻 Developer**  | Sachin Arora                      |
| **📧 Email**      | [sachnaror@gmail.com](mailto:sacinaror@gmail.com) |
| **📍 Location**   | Noida, India                       |
| **📂 GitHub**     | [Link](https://github.com/sachnaror) |
| **🌐 Youtube**    | [Link](https://www.youtube.com/@sachnaror4841/videos) |
| **🌐 Blog**       | [Link](https://medium.com/@schnaror) |
| **🌐 Website**    | [Link](https://about.me/sachin-arora) |
| **🌐 Twitter**    | [Link](https://twitter.com/sachinhep) |
| **📱 Phone**      | [+91 9560330483](tel:+919560330483) |


------------------------------------------------------------------------
