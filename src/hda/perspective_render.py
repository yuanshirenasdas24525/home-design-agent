# src/hda/perspective_render.py
from __future__ import annotations
from hda.models import Scheme
from hda.providers.base import ImageProvider


def render_perspectives(image: ImageProvider, scheme: Scheme,
                        reference_svg: str) -> dict[str, bytes]:
    """⑤ 每个有 render_prompt 的房间出一张实景图。返回 room_id -> 图片字节。"""
    out: dict[str, bytes] = {}
    for rs in scheme.rooms:
        if not rs.render_prompt:
            continue
        out[rs.room_id] = image.render_perspective(
            prompt=rs.render_prompt, reference_svg=reference_svg)
    return out
