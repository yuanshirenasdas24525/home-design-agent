from __future__ import annotations
from typing import Literal
from pydantic import BaseModel

Point = tuple[float, float]


class Room(BaseModel):
    room_id: str
    name: str
    area: float
    polygon: list[Point]  # 房间边界，米为单位


class Door(BaseModel):
    room_a: str
    room_b: str | None = None  # None 表示通向户外/入户门
    pos: Point


class Window(BaseModel):
    room_id: str
    pos: Point


class FloorPlan(BaseModel):
    community: str = ""          # 小区名
    layout_type: str = ""        # 户型，如 "三室两厅"
    total_area: float = 0.0
    rooms: list[Room]
    doors: list[Door] = []
    windows: list[Window] = []


class Requirement(BaseModel):
    style: str = ""              # 风格
    budget_level: Literal["低", "中", "高"] = "中"
    household: str = ""          # 居住人口描述
    constraints: list[str] = []  # 硬约束
    preferences: list[str] = []  # 软偏好


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
