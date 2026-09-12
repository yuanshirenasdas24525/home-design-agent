from __future__ import annotations
import base64
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from hda.pipeline import Pipeline
from hda.providers.base import Provider

_STATIC = Path(__file__).parent / "static"


def create_app(provider: Provider) -> FastAPI:
    app = FastAPI(title="户型效果预览 Agent")
    pipe = Pipeline(provider)

    @app.get("/", response_class=HTMLResponse)
    def index():
        return (_STATIC / "index.html").read_text(encoding="utf-8")

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
