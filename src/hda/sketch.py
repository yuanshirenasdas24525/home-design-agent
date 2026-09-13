# src/hda/sketch.py
from __future__ import annotations
from io import BytesIO
from hda.models import Room, RoomScheme, Window

_HEIGHTS = [
    (("衣柜", "橱柜", "冰箱", "书架", "鞋柜", "吊柜"), 2.0),
    (("床",), 0.5), (("沙发", "茶几", "电视柜", "餐桌", "书桌", "梳妆台", "洗手台"), 0.8),
    (("马桶", "灶台", "水槽", "餐椅", "休闲椅", "床头柜"), 0.6),
]
# 窗型 → (下沿高, 上沿高, 半宽) 米；阳台门/落地为落地
_WIN = {"普通": (0.9, 2.2, 0.8), "飘窗": (0.5, 1.9, 1.0),
        "落地": (0.02, 2.4, 0.9), "阳台门": (0.02, 2.4, 1.2)}


def _height(item: str) -> float:
    for kws, h in _HEIGHTS:
        if any(k in item for k in kws):
            return h
    return 0.7


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _primary_wall(room: Room, windows: list[Window]):
    """选一个"主开口"所在的墙，把它转到正对镜头的背墙。优先阳台门/落地窗。"""
    xs = [p[0] for p in room.polygon]
    ys = [p[1] for p in room.polygon]
    minx, miny, maxx, maxy = min(xs), min(ys), max(xs), max(ys)
    W, D = (maxx - minx) or 1.0, (maxy - miny) or 1.0
    mine = [w for w in windows if w.room_id == room.room_id]
    if not mine:
        return "back", None, W, D
    order = {"阳台门": 0, "落地": 1, "飘窗": 2, "普通": 3}
    win = sorted(mine, key=lambda w: order.get(w.kind, 3))[0]
    u, v = win.pos[0] - minx, win.pos[1] - miny
    dists = {"left": u, "right": W - u, "near": v, "back": D - v}
    wall = min(dists, key=dists.get)
    return wall, win, W, D


def _orient(wall, W, D):
    """返回 (transform(u,v)->(across,depth), A, Dp)；把 wall 变成背墙(depth=Dp)。"""
    if wall == "back":
        return (lambda u, v: (u, v)), W, D
    if wall == "near":
        return (lambda u, v: (W - u, D - v)), W, D
    if wall == "left":
        return (lambda u, v: (v, W - u)), D, W
    return (lambda u, v: (D - v, u)), D, W  # right


def _primitives(room, rs, windows, W_img, H_img):
    xs = [p[0] for p in room.polygon]
    ys = [p[1] for p in room.polygon]
    minx, miny = min(xs), min(ys)
    wall, win, W, D = _primary_wall(room, windows)
    tf, A, Dp = _orient(wall, W, D)
    Hm = 2.8

    m = 60
    NTL, NTR, NBL, NBR = (m, m), (W_img - m, m), (m, H_img - m), (W_img - m, H_img - m)
    vp = (W_img / 2, H_img / 2)
    t = 0.42
    BTL, BTR = _lerp(NTL, vp, t), _lerp(NTR, vp, t)
    BBL, BBR = _lerp(NBL, vp, t), _lerp(NBR, vp, t)

    def fl(a, d):
        A_, b = a / A, d / Dp
        return _lerp(_lerp(NBL, BBL, b), _lerp(NBR, BBR, b), A_)

    def ce(a, d):
        A_, b = a / A, d / Dp
        return _lerp(_lerp(NTL, BTL, b), _lerp(NTR, BTR, b), A_)

    def up(a, d, h):
        return _lerp(fl(a, d), ce(a, d), min(h / Hm, 1.0))

    P = []
    for p, q in [(NTL, NTR), (NBL, NBR), (NTL, NBL), (NTR, NBR),
                 (BTL, BTR), (BBL, BBR), (BTL, BBL), (BTR, BBR),
                 (NTL, BTL), (NTR, BTR), (NBL, BBL), (NBR, BBR)]:
        P.append(("line", p, q))

    # 窗：画在背墙，按类型
    if win is not None:
        aw = tf(win.pos[0] - minx, win.pos[1] - miny)[0]
        lo, hi, hw = _WIN.get(win.kind, _WIN["普通"])
        aL, aR = max(aw - hw, 0.05), min(aw + hw, A - 0.05)
        P.append(("win", [up(aL, Dp, hi), up(aR, Dp, hi), up(aR, Dp, lo), up(aL, Dp, lo)]))
        if win.kind == "飘窗":  # 窗台横线，提示非落地
            P.append(("line", up(aL, Dp, lo), up(aR, Dp, lo)))

    # 家具：实心块
    for f in (rs.furniture if rs else []):
        w = f.size[0] if len(f.size) > 0 else 0.6
        dep = f.size[1] if len(f.size) > 1 else 0.6
        ca, cd = tf(f.pos[0] - minx, f.pos[1] - miny)
        aw, dw = (w, dep) if wall in ("back", "near") else (dep, w)
        a0, a1 = max(ca - aw / 2, 0), min(ca + aw / 2, A)
        d0, d1 = max(cd - dw / 2, 0), min(cd + dw / 2, Dp)
        if d1 <= d0 or a1 <= a0:
            continue
        h = _height(f.item)
        b0, b1, b2, b3 = fl(a0, d0), fl(a1, d0), fl(a1, d1), fl(a0, d1)
        t0, t1, t2, t3 = up(a0, d0, h), up(a1, d0, h), up(a1, d1, h), up(a0, d1, h)
        P.append(("fill", [t0, t1, t2, t3], (205, 205, 205)))   # 顶面
        P.append(("fill", [b0, b1, t1, t0], (185, 185, 185)))   # 前面
        P.append(("fill", [b1, b2, t2, t1], (165, 165, 165)))   # 侧面
        for a, bb in [(b0, b1), (b1, b2), (b2, b3), (b3, b0),
                      (t0, t1), (t1, t2), (t2, t3), (t3, t0),
                      (b0, t0), (b1, t1), (b2, t2), (b3, t3)]:
            P.append(("line", a, bb))
    return P


def _svg(prims, W_img, H_img):
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W_img} {H_img}">',
           f'<rect width="{W_img}" height="{H_img}" fill="#ffffff"/>']
    for kind, *a in prims:
        if kind == "line":
            (x1, y1), (x2, y2) = a
            out.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#333" stroke-width="2"/>')
        elif kind == "win":
            pts = " ".join(f"{x:.0f},{y:.0f}" for x, y in a[0])
            out.append(f'<polygon points="{pts}" fill="#dceaf5" stroke="#5b8db0" stroke-width="2"/>')
        else:  # fill
            pts = " ".join(f"{x:.0f},{y:.0f}" for x, y in a[0])
            r, g, b = a[1]
            out.append(f'<polygon points="{pts}" fill="rgb({r},{g},{b})" stroke="#555" stroke-width="1"/>')
    out.append("</svg>")
    return "\n".join(out)


def render_room_sketch(room, rs, windows, W_img=1024, H_img=768) -> str:
    return _svg(_primitives(room, rs, windows, W_img, H_img), W_img, H_img)


def render_room_sketch_png(room, rs, windows, W_img=1024, H_img=768) -> bytes:
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W_img, H_img), "white")
    dr = ImageDraw.Draw(img)
    for kind, *a in _primitives(room, rs, windows, W_img, H_img):
        if kind == "line":
            dr.line([a[0], a[1]], fill=(40, 40, 40), width=3)
        elif kind == "win":
            dr.polygon([tuple(p) for p in a[0]], fill=(220, 234, 245), outline=(91, 141, 176))
        else:
            dr.polygon([tuple(p) for p in a[0]], fill=a[1], outline=(85, 85, 85))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
