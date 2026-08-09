from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.db.connection import get_connection

app = FastAPI(title="Portfolio Monitor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def query(sql, params=()):
    conn = get_connection()
    return [dict(r) for r in conn.execute(sql, params).fetchall()]

@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}

@app.get("/api/findings/{date}")
def findings(date: str, status: str | None = None):
    sql = "SELECT * FROM findings WHERE run_date = ?"
    params = [date]
    if status:
        sql += " AND status = ?"
        params.append(status)
    return query(sql, tuple(params))


@app.get("/api/new-holdings/{date}")
def new_holdings(date: str):
    return query(
        "SELECT * FROM findings WHERE run_date = ? AND is_new = 1", (date,)
    )


@app.get("/api/events/{date}")
def events(date: str):
    return query("SELECT * FROM corporate_events WHERE date = ?", (date,))


@app.get("/api/summary/{date}")
def summary(date: str):
    rows = query(
        "SELECT status, COUNT(*) AS n FROM findings WHERE run_date = ? GROUP BY status",
        (date,),
    )
    return {r["status"]: r["n"] for r in rows}