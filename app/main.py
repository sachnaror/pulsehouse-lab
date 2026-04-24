from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .clickhouse_service import AnalyticsRepository, CREATE_TABLE_SQL


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="PulseHouse Lab")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
repo = AnalyticsRepository()


@app.on_event("startup")
def startup_event() -> None:
    repo.ensure_seeded()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "schema_sql": CREATE_TABLE_SQL.strip(),
        },
    )


@app.get("/api/overview")
def get_overview():
    return JSONResponse(repo.overview())


@app.get("/api/timeseries")
def get_timeseries():
    return JSONResponse(repo.timeseries())


@app.get("/api/top-endpoints")
def get_top_endpoints():
    return JSONResponse(repo.top_endpoints())


@app.get("/api/anomalies")
def get_anomalies():
    return JSONResponse(repo.anomalies())


@app.get("/api/explain")
def get_explanation():
    return JSONResponse({"message": repo.explanation()})
