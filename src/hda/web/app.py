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

_STATIC = Path(__file__).parent / "static"


class PlanRequest(BaseModel):
    floorplan: FloorPlan
    scheme: Scheme | None = None


def create_app(provider: Provider) -> FastAPI:
    app = FastAPI(title="户型效果预览 Agent")
    pipe = Pipeline(provider)

    @app.get("/", response_class=HTMLResponse)
    def index():
        return (_STATIC / "index.html").read_text(encoding="utf-8")

    @app.get("/trace", response_class=HTMLResponse)
    def trace():
        return (_STATIC / "trace.html").read_text(encoding="utf-8")

    @app.post("/api/render_plan")
    def render_plan(req: PlanRequest):
        """从描线得到的户型几何渲染彩平图（几何来自真图描线，天然对得上）。"""
        scheme = req.scheme or Scheme(scheme_id="trace", floorplan_ref="trace")
        svg = render_colored_plan(req.floorplan, scheme)
        return JSONResponse({"colored_plan_svg": svg})

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
