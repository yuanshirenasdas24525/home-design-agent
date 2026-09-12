# src/hda/grid.py
from __future__ import annotations
from hda.models import GridPlan, FloorPlan, Room


def _cumulative(dims: list[float]) -> list[float]:
    xs = [0.0]
    for d in dims:
        xs.append(xs[-1] + d)
    return xs


def build_grid_lines(gp: GridPlan) -> tuple[list[float], list[float]]:
    """从四条尺寸链拼出网格线（米）。顶/底并集为竖线，左/右并集为横线。"""
    xset = set(_cumulative(gp.top_dims)) | set(_cumulative(gp.bottom_dims))
    yset = set(_cumulative(gp.left_dims)) | set(_cumulative(gp.right_dims))
    x_lines = sorted(v / 1000.0 for v in xset)
    y_lines = sorted(v / 1000.0 for v in yset)
    return x_lines, y_lines


def _nearest_index(lines: list[float], value: float) -> int:
    return min(range(len(lines)), key=lambda i: abs(lines[i] - value))


def snap_rooms(gp: GridPlan, x_lines: list[float], y_lines: list[float]) -> FloorPlan:
    """把每个房间的归一化 bbox 吸附到网格线，得到与尺寸一致的矩形几何。

    房间的相对位置来自视觉模型（大致），精确坐标来自尺寸链网格——
    因此结果与图上标注一致，个别错放由用户在网格上点选修正。
    """
    rooms_in = [r for r in gp.rooms if len(r.bbox) == 4]
    if not rooms_in or len(x_lines) < 2 or len(y_lines) < 2:
        return FloorPlan(rooms=[])

    bx0 = min(r.bbox[0] for r in rooms_in)
    by0 = min(r.bbox[1] for r in rooms_in)
    bx1 = max(r.bbox[2] for r in rooms_in)
    by1 = max(r.bbox[3] for r in rooms_in)
    span_x = (bx1 - bx0) or 1.0
    span_y = (by1 - by0) or 1.0
    total_x, total_y = x_lines[-1], y_lines[-1]

    rooms: list[Room] = []
    for i, r in enumerate(rooms_in):
        mx0 = (r.bbox[0] - bx0) / span_x * total_x
        mx1 = (r.bbox[2] - bx0) / span_x * total_x
        my0 = (r.bbox[1] - by0) / span_y * total_y
        my1 = (r.bbox[3] - by0) / span_y * total_y
        c0, c1 = _nearest_index(x_lines, mx0), _nearest_index(x_lines, mx1)
        r0, r1 = _nearest_index(y_lines, my0), _nearest_index(y_lines, my1)
        if c1 <= c0:
            c1 = min(c0 + 1, len(x_lines) - 1)
        if r1 <= r0:
            r1 = min(r0 + 1, len(y_lines) - 1)
        x0, x1 = x_lines[c0], x_lines[c1]
        y0, y1 = y_lines[r0], y_lines[r1]
        rooms.append(Room(
            room_id=f"r{i + 1}", name=r.name, area=r.area,
            polygon=[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))
    return FloorPlan(total_area=sum(r.area for r in rooms_in), rooms=rooms)
