# src/hda/plan_renderer.py
from __future__ import annotations
from hda.models import FloorPlan, Scheme

SCALE = 100  # 1 米 = 100 像素
PAD = 56

# 房间填色（循环取用），柔和可区分
_ROOM_FILLS = [
    "#eaf1e6", "#f3ead9", "#e7eef5", "#f5e9e6", "#eee7f2",
    "#e6f1f0", "#f5f1e0", "#ecebe5", "#f0e8ee", "#e8eef0",
]


def _bounds(fp: FloorPlan):
    xs = [p[0] for r in fp.rooms for p in r.polygon]
    ys = [p[1] for r in fp.rooms for p in r.polygon]
    return min(xs), min(ys), max(xs), max(ys)


def render_colored_plan(floorplan: FloorPlan, scheme: Scheme) -> str:
    """④ 从户型几何 + Scheme 程序化渲染 2D 彩平图（纯逻辑，零 AI）。

    房间按几何精确绘制，家具/门/窗叠加其上。几何来自识别+人工校正，
    因此彩平图与真实户型一一对应，墙体绝不跑偏。
    """
    minx, miny, maxx, maxy = _bounds(floorplan)
    w = (maxx - minx) * SCALE + PAD * 2
    h = (maxy - miny) * SCALE + PAD * 2

    def sx(x): return (x - minx) * SCALE + PAD
    def sy(y): return (y - miny) * SCALE + PAD

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
        f'font-family="-apple-system, PingFang SC, sans-serif">',
        f'<rect width="{w:.0f}" height="{h:.0f}" fill="#ffffff"/>',
    ]

    # 1) 房间：填色 + 墙体描边 + 名称/面积
    for i, room in enumerate(floorplan.rooms):
        pts = " ".join(f"{sx(x):.0f},{sy(y):.0f}" for x, y in room.polygon)
        fill = _ROOM_FILLS[i % len(_ROOM_FILLS)]
        parts.append(f'<polygon points="{pts}" fill="{fill}" '
                     f'stroke="#2f2f2f" stroke-width="6" stroke-linejoin="miter"/>')
        cx = sum(sx(x) for x, _ in room.polygon) / len(room.polygon)
        cy = sum(sy(y) for _, y in room.polygon) / len(room.polygon)
        parts.append(f'<text x="{cx:.0f}" y="{cy - 6:.0f}" font-size="17" '
                     f'font-weight="600" text-anchor="middle" fill="#2a2a2a">{room.name}</text>')
        if room.area:
            parts.append(f'<text x="{cx:.0f}" y="{cy + 14:.0f}" font-size="13" '
                         f'text-anchor="middle" fill="#7a7a7a">{room.area:g}㎡</text>')

    # 2) 家具（来自 Scheme），pos 视为中心
    for rs in scheme.rooms:
        for f in rs.furniture:
            fw = (f.size[0] if len(f.size) > 0 else 0.6) * SCALE
            fh = (f.size[1] if len(f.size) > 1 else 0.6) * SCALE
            fx = sx(f.pos[0]) - fw / 2
            fy = sy(f.pos[1]) - fh / 2
            parts.append(f'<rect x="{fx:.0f}" y="{fy:.0f}" width="{fw:.0f}" '
                         f'height="{fh:.0f}" fill="#c9b79c" '
                         f'stroke="#8a7a5c" stroke-width="1.5" rx="4" opacity="0.92"/>')
            if fw > 40 and fh > 26:
                parts.append(f'<text x="{sx(f.pos[0]):.0f}" y="{sy(f.pos[1]) + 4:.0f}" '
                             f'font-size="10" text-anchor="middle" fill="#5a4a2c">{f.item}</text>')

    # 3) 窗：外墙上的浅蓝短段
    for win in floorplan.windows:
        x, y = sx(win.pos[0]), sy(win.pos[1])
        parts.append(f'<rect x="{x - 26:.0f}" y="{y - 5:.0f}" width="52" height="10" '
                     f'fill="#bcd4e6" stroke="#5b8db0" stroke-width="1.5"/>')

    # 4) 门：门洞处的开启弧线
    for d in floorplan.doors:
        x, y = sx(d.pos[0]), sy(d.pos[1])
        r = 34
        parts.append(f'<path d="M{x:.0f},{y:.0f} L{x + r:.0f},{y:.0f} '
                     f'A{r},{r} 0 0 1 {x:.0f},{y + r:.0f}" fill="none" '
                     f'stroke="#b08a5b" stroke-width="1.5"/>')
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3" fill="#b08a5b"/>')

    parts.append("</svg>")
    return "\n".join(parts)
