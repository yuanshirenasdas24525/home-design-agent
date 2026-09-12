from __future__ import annotations
import base64
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from hda.pipeline import Pipeline
from hda.providers.base import Provider
from hda.models import FloorPlan, Scheme
from hda.plan_renderer import render_colored_plan
from hda.grid import build_grid_lines, snap_rooms
from hda.store import CaseStore

_STATIC = Path(__file__).parent / "static"


class PlanRequest(BaseModel):
    floorplan: FloorPlan
    scheme: Scheme | None = None


class DesignRequest(BaseModel):
    floorplan: FloorPlan
    options: dict = {}
    transcript: str = ""


class SaveCaseRequest(BaseModel):
    community: str = ""
    layout_type: str = ""
    style: str = ""
    floorplan: FloorPlan
    scheme: Scheme
    svg: str = ""


def create_app(provider: Provider, store: CaseStore | None = None) -> FastAPI:
    app = FastAPI(title="户型效果预览 Agent")
    pipe = Pipeline(provider)
    store = store or CaseStore()

    @app.get("/", response_class=HTMLResponse)
    def index():
        return (_STATIC / "index.html").read_text(encoding="utf-8")

    @app.get("/trace", response_class=HTMLResponse)
    def trace():
        return (_STATIC / "trace.html").read_text(encoding="utf-8")

    @app.post("/api/render_plan")
    def render_plan(req: PlanRequest):
        """从户型几何渲染彩平图（几何来自尺寸网格，天然对得上）。"""
        scheme = req.scheme or Scheme(scheme_id="plan", floorplan_ref="plan")
        svg = render_colored_plan(req.floorplan, scheme)
        return JSONResponse({"colored_plan_svg": svg})

    @app.get("/grid", response_class=HTMLResponse)
    def grid_page():
        return (_STATIC / "grid.html").read_text(encoding="utf-8")

    @app.post("/api/design")
    def design(req: DesignRequest):
        """从已校正几何 + 需求 出带家具的软装平面方案（②③④，锚定几何）。"""
        _, scheme, svg = pipe.design_from_floorplan(
            req.floorplan, req.options, req.transcript)
        return JSONResponse({
            "colored_plan_svg": svg,
            "scheme": scheme.model_dump(),
        })

    @app.get("/cases", response_class=HTMLResponse)
    def cases_page():
        return (_STATIC / "cases.html").read_text(encoding="utf-8")

    @app.post("/api/save_case")
    def save_case(req: SaveCaseRequest):
        """整包落库（⑦）：小区+户型+风格 为索引，供历史预览与同小区参考。"""
        cid = store.save(req.community, req.layout_type, req.style,
                         req.floorplan, req.scheme, req.svg)
        return JSONResponse({"id": cid})

    @app.get("/api/cases")
    def list_cases(community: str = "", layout_type: str = "", style: str = ""):
        return JSONResponse({"cases": store.list(community, layout_type, style)})

    @app.get("/api/cases/{cid}")
    def get_case(cid: str):
        case = store.get(cid)
        if case is None:
            return JSONResponse({"error": "not found"}, status_code=404)
        return JSONResponse(case)

    @app.post("/api/extract_dims")
    async def extract_dims(image: UploadFile = File(...)):
        """读图上尺寸链 + 房间 → 拼网格 → 吸附出初始几何，供用户在网格上确认修正。"""
        img_bytes = await image.read()
        gp = provider.extract_grid(img_bytes)
        x_lines, y_lines = build_grid_lines(gp)
        fp = snap_rooms(gp, x_lines, y_lines)
        return JSONResponse({
            "dims": gp.model_dump(),        # 四条尺寸链 + 房间(可编辑)
            "x_lines": x_lines,             # 竖线位置（米）
            "y_lines": y_lines,             # 横线位置（米）
            "floorplan": fp.model_dump(),   # 吸附后的初始几何
        })

    @app.post("/api/preview")
    async def preview(image: UploadFile = File(...), community: str = Form(""),
                      style: str = Form(""), transcript: str = Form("")):
        img_bytes = await image.read()
        result = pipe.run(image_bytes=img_bytes, community=community,
                          options={"style": style}, transcript=transcript)
        perspectives = {
            rid: "data:image/png;base64," + base64.b64encode(b).decode()
            for rid, b in result.perspectives.items()
        }
        return JSONResponse({
            "colored_plan_svg": result.colored_plan_svg,
            "perspectives": perspectives,
            "scheme": result.scheme.model_dump(),
        })

    return app
