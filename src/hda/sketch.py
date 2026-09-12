# src/hda/sketch.py
from __future__ import annotations
from io import BytesIO
from hda.models import Room, RoomScheme, Window

# 家具高度估计（米），按名称关键词
_HEIGHTS = [
    (("衣柜", "橱柜", "冰箱", "书架", "鞋柜", "吊柜"), 2.0),
    (("床",), 0.5), (("沙发", "茶几", "电视柜", "餐桌", "书桌", "梳妆台", "洗手台"), 0.8),
    (("马桶", "灶台", "水槽", "餐椅", "休闲椅", "床头柜"), 0.6),
]


def _height(item: str) -> float:
    for kws, h in _HEIGHTS:
        if any(k in item for k in kws):
            return h
    return 0.7


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _primitives(room: Room, rs: RoomScheme | None, windows: list[Window],
                W_img: int, H_img: int):
    """算出一点透视下的图元：('line',p,q) 与 ('poly',pts)。SVG/PNG 共用。"""
    xs = [p[0] for p in room.polygon]
    ys = [p[1] for p in room.polygon]
    minx, miny, maxx, maxy = min(xs), min(ys), max(xs), max(ys)
    Wm, Dm, Hm = (maxx - minx) or 1.0, (maxy - miny) or 1.0, 2.8

    m = 60
    NTL, NTR = (m, m), (W_img - m, m)
    NBL, NBR = (m, H_img - m), (W_img - m, H_img - m)
    vp = (W_img / 2, H_img / 2)
    t = 0.42
    BTL, BTR = _lerp(NTL, vp, t), _lerp(NTR, vp, t)
    BBL, BBR = _lerp(NBL, vp, t), _lerp(NBR, vp, t)

    def floor_pt(u, v):
        a, b = u / Wm, v / Dm
        return _lerp(_lerp(NBL, BBL, b), _lerp(NBR, BBR, b), a)

    def ceil_pt(u, v):
        a, b = u / Wm, v / Dm
        return _lerp(_lerp(NTL, BTL, b), _lerp(NTR, BTR, b), a)

    def up(u, v, h):
        return _lerp(floor_pt(u, v), ceil_pt(u, v), min(h / Hm, 1.0))

    prims: list = []
    # 房间盒子
    for p, q in [(NTL, NTR), (NBL, NBR), (NTL, NBL), (NTR, NBR),
                 (BTL, BTR), (BBL, BBR), (BTL, BBL), (BTR, BBR),
                 (NTL, BTL), (NTR, BTR), (NBL, BBL), (NBR, BBR)]:
        prims.append(("line", p, q))
    # 窗（近似画在后墙）
    for win in windows:
        if win.room_id != room.room_id:
            continue
        u = min(max(win.pos[0] - minx, 0), Wm)
        pts = [up(max(u - 0.7, 0), Dm, 2.2), up(min(u + 0.7, Wm), Dm, 2.2),
               up(min(u + 0.7, Wm), Dm, 0.9), up(max(u - 0.7, 0), Dm, 0.9)]
        prims.append(("poly", pts))
    # 家具体块
    for f in (rs.furniture if rs else []):
        w = f.size[0] if len(f.size) > 0 else 0.6
        d = f.size[1] if len(f.size) > 1 else 0.6
        cx, cy = f.pos[0] - minx, f.pos[1] - miny
        u0, u1 = max(cx - w / 2, 0), min(cx + w / 2, Wm)
        v0, v1 = max(cy - d / 2, 0), min(cy + d / 2, Dm)
        h = _height(f.item)
        b = [floor_pt(u0, v0), floor_pt(u1, v0), floor_pt(u1, v1), floor_pt(u0, v1)]
        tp = [up(u0, v0, h), up(u1, v0, h), up(u1, v1, h), up(u0, v1, h)]
        for i in range(4):
            prims.append(("line", b[i], b[(i + 1) % 4]))
            prims.append(("line", tp[i], tp[(i + 1) % 4]))
            prims.append(("line", b[i], tp[i]))
    return prims


def render_room_sketch(room: Room, rs: RoomScheme | None,
                       windows: list[Window], W_img=1024, H_img=768) -> str:
    """一点透视结构图（SVG，用于展示/调试）。"""
    prims = _primitives(room, rs, windows, W_img, H_img)
    P = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W_img} {H_img}">',
         f'<rect width="{W_img}" height="{H_img}" fill="#ffffff"/>']
    for kind, *a in prims:
        if kind == "line":
            (x1, y1), (x2, y2) = a
            P.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                     f'stroke="#333" stroke-width="2"/>')
        else:
            pts = " ".join(f"{x:.0f},{y:.0f}" for x, y in a[0])
            P.append(f'<polygon points="{pts}" fill="#dceaf5" stroke="#5b8db0" stroke-width="2"/>')
    P.append("</svg>")
    return "\n".join(P)


def render_room_sketch_png(room: Room, rs: RoomScheme | None,
                           windows: list[Window], W_img=1024, H_img=768) -> bytes:
    """一点透视结构图（PNG 字节，喂给通义万相 doodle）。用 Pillow，无系统依赖。"""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W_img, H_img), "white")
    dr = ImageDraw.Draw(img)
    for kind, *a in _primitives(room, rs, windows, W_img, H_img):
        if kind == "line":
            dr.line([a[0], a[1]], fill=(40, 40, 40), width=3)
        else:
            dr.polygon([tuple(p) for p in a[0]], fill=(220, 234, 245), outline=(91, 141, 176))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
