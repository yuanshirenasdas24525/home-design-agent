from __future__ import annotations
import re
from typing import Literal
from pydantic import BaseModel, field_validator

Point = tuple[float, float]


def _coerce_float(v):
    """容错：把 '31.03平方米' / '3.85m' 这类带单位字符串提取成数字。"""
    if isinstance(v, str):
        m = re.search(r"-?\d+(?:\.\d+)?", v)
        if m:
            return float(m.group())
    return v


class Room(BaseModel):
    room_id: str
    name: str
    area: float
    polygon: list[Point] = []  # 房间边界，米为单位（识别可能缺省）

    _v_area = field_validator("area", mode="before")(_coerce_float)


class Door(BaseModel):
    room_a: str
    room_b: str | None = None  # None 表示通向户外/入户门
    pos: Point


class Window(BaseModel):
    room_id: str
    pos: Point
    kind: str = "普通"  # 普通 / 飘窗 / 落地 / 阳台门（通向阳台的落地推拉门）


class FloorPlan(BaseModel):
    community: str = ""          # 小区名
    layout_type: str = ""        # 户型，如 "三室两厅"
    total_area: float = 0.0
    rooms: list[Room]
    doors: list[Door] = []
    windows: list[Window] = []

    _v_total = field_validator("total_area", mode="before")(_coerce_float)


class Requirement(BaseModel):
    style: str = ""              # 风格
    budget_level: Literal["低", "中", "高"] = "中"
    household: str = ""          # 居住人口描述
    constraints: list[str] = []  # 硬约束
    preferences: list[str] = []  # 软偏好


class GridRoom(BaseModel):
    """视觉模型读出的单个房间：名称、面积、以及在整图中的相对包围盒 [x0,y0,x1,y1]（0~1）。"""
    name: str
    area: float = 0.0
    bbox: list[float] = []  # [x0, y0, x1, y1] 归一化，左上为原点

    _v_area = field_validator("area", mode="before")(_coerce_float)


class GridPlan(BaseModel):
    """视觉模型读出的"尺寸链 + 房间"，用于半自动拼装几何。"""
    top_dims: list[float] = []      # 顶部尺寸链（毫米，左→右）
    bottom_dims: list[float] = []   # 底部（左→右）
    left_dims: list[float] = []     # 左侧（上→下）
    right_dims: list[float] = []    # 右侧（上→下）
    rooms: list[GridRoom] = []


class FurnitureItem(BaseModel):
    item: str
    pos: Point
    facing: str = ""
    size: list[float] = []  # [长, 宽] 或 [长, 宽, 高]（米）；平面渲染取前两维，第三维供 3D 阶段用


class RoomScheme(BaseModel):
    room_id: str
    name: str
    furniture: list[FurnitureItem] = []
    finishes: dict[str, str] = {}
    soft: list[str] = []
    render_prompt: str = ""


class ConstraintCheck(BaseModel):
    rule: str
    status: Literal["pass", "fail"]


class Scheme(BaseModel):
    scheme_id: str
    floorplan_ref: str
    style: str = ""
    palette: list[str] = []
    budget_level: str = "中"
    rooms: list[RoomScheme] = []
    constraints_check: list[ConstraintCheck] = []

    def get_room(self, room_id: str) -> RoomScheme | None:
        return next((r for r in self.rooms if r.room_id == room_id), None)
