# src/hda/store.py
from __future__ import annotations
import json
import sqlite3
import time
import uuid
from pathlib import Path
from hda.models import FloorPlan, Scheme

DEFAULT_DB = "data/cases.db"


class CaseStore:
    """案例库存储：每次生产整包落库，按 小区+户型+风格 检索（⑦）。"""

    def __init__(self, db_path: str | Path = DEFAULT_DB):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS cases(
                id TEXT PRIMARY KEY, community TEXT, layout_type TEXT, style TEXT,
                floorplan TEXT, scheme TEXT, svg TEXT, created_at REAL)""")

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def save(self, community: str, layout_type: str, style: str,
             floorplan: FloorPlan, scheme: Scheme, svg: str) -> str:
        cid = uuid.uuid4().hex[:12]
        with self._conn() as c:
            c.execute("INSERT INTO cases VALUES(?,?,?,?,?,?,?,?)", (
                cid, community, layout_type, style,
                floorplan.model_dump_json(), scheme.model_dump_json(), svg, time.time()))
        return cid

    def list(self, community: str = "", layout_type: str = "", style: str = "",
             limit: int = 50) -> list[dict]:
        q = "SELECT id,community,layout_type,style,created_at FROM cases WHERE 1=1"
        args: list = []
        if community:
            q += " AND community=?"; args.append(community)
        if layout_type:
            q += " AND layout_type=?"; args.append(layout_type)
        if style:
            q += " AND style=?"; args.append(style)
        q += " ORDER BY created_at DESC LIMIT ?"; args.append(limit)
        keys = ["id", "community", "layout_type", "style", "created_at"]
        with self._conn() as c:
            return [dict(zip(keys, row)) for row in c.execute(q, args).fetchall()]

    def get(self, cid: str) -> dict | None:
        keys = ["id", "community", "layout_type", "style", "floorplan", "scheme", "svg"]
        with self._conn() as c:
            row = c.execute(
                "SELECT id,community,layout_type,style,floorplan,scheme,svg "
                "FROM cases WHERE id=?", (cid,)).fetchone()
        if not row:
            return None
        d = dict(zip(keys, row))
        d["floorplan"] = json.loads(d["floorplan"])
        d["scheme"] = json.loads(d["scheme"])
        return d
