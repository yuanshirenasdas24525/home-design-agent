# src/hda/realistic.py
from __future__ import annotations
from hda.models import FloorPlan, Scheme
from hda.sketch import render_room_sketch_png

# 只给"值得出实景"的主要空间渲染，跳过阳台等（可扩展）
_SKIP = ("阳台", "飘窗")


def _prompt_for(room_name: str, style: str) -> str:
    return f"{style}风格{room_name}室内实景照片，高清写实，自然采光，精装修"


def render_room_realistic(floorplan: FloorPlan, scheme: Scheme, wanx,
                          style: str = "现代简约",
                          room_ids: list[str] | None = None) -> dict[str, bytes]:
    """逐房间：几何+家具 → 结构线稿 → 通义万相 doodle → 与户型对上的实景图。

    wanx 需实现 doodle(sketch_png: bytes, prompt: str) -> bytes。
    room_ids 给定则只渲这些房间（省额度）。返回 room_id -> 图片字节。
    """
    rooms_by_id = {r.room_id: r for r in floorplan.rooms}
    out: dict[str, bytes] = {}
    for rs in scheme.rooms:
        if room_ids is not None and rs.room_id not in room_ids:
            continue
        if any(k in rs.name for k in _SKIP):
            continue
        room = rooms_by_id.get(rs.room_id)
        if room is None or not room.polygon:
            continue
        sketch_png = render_room_sketch_png(room, rs, floorplan.windows)
        out[rs.room_id] = wanx.doodle(sketch_png, _prompt_for(rs.name, style))
    return out
