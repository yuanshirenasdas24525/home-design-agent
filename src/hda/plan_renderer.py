# src/hda/plan_renderer.py
from __future__ import annotations
from hda.models import FloorPlan, Scheme

SCALE = 100  # 1 米 = 100 像素
PAD = 40


def _bounds(fp: FloorPlan):
    xs = [p[0] for r in fp.rooms for p in r.polygon]
    ys = [p[1] for r in fp.rooms for p in r.polygon]
    return min(xs), min(ys), max(xs), max(ys)


def render_colored_plan(floorplan: FloorPlan, scheme: Scheme) -> str:
    """④ 从 Scheme 坐标程序化渲染 2D 彩平图（纯逻辑，零 AI）。"""
    minx, miny, maxx, maxy = _bounds(floorplan)
    w = (maxx - minx) * SCALE + PAD * 2
    h = (maxy - miny) * SCALE + PAD * 2

    def sx(x): return (x - minx) * SCALE + PAD
    def sy(y): return (y - miny) * SCALE + PAD

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
        f'font-family="sans-serif">',
        f'<rect width="{w:.0f}" height="{h:.0f}" fill="#faf8f5"/>',
    ]

    for room in floorplan.rooms:
        pts = " ".join(f"{sx(x):.0f},{sy(y):.0f}" for x, y in room.polygon)
        parts.append(f'<polygon points="{pts}" fill="#f0ead9" '
                     f'stroke="#4a4a4a" stroke-width="3"/>')
        cx = sum(sx(x) for x, _ in room.polygon) / len(room.polygon)
        cy = sum(sy(y) for _, y in room.polygon) / len(room.polygon)
        parts.append(f'<text x="{cx:.0f}" y="{cy:.0f}" font-size="16" '
                     f'text-anchor="middle" fill="#333">{room.name}</text>')

    for rs in scheme.rooms:
        for f in rs.furniture:
            fx, fy = sx(f.pos[0]), sy(f.pos[1])
            # size 可能为 []、[长] 或 [长,宽,高]，平面只取前两维，缺省给 0.8m
            fw = (f.size[0] if len(f.size) > 0 else 0.8) * SCALE
            fh = (f.size[1] if len(f.size) > 1 else 0.8) * SCALE
            parts.append(f'<rect x="{fx:.0f}" y="{fy:.0f}" width="{fw:.0f}" '
                         f'height="{fh:.0f}" fill="#c9b79c" stroke="#8a7a5c" '
                         f'rx="4" opacity="0.9"/>')
            parts.append(f'<text x="{fx + fw / 2:.0f}" y="{fy + fh / 2:.0f}" '
                         f'font-size="11" text-anchor="middle" fill="#5a4a2c">{f.item}</text>')

    parts.append("</svg>")
    return "\n".join(parts)
