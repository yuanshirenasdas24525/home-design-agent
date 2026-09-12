from __future__ import annotations
from hda.models import (
    FloorPlan, Room, Door, Window, Requirement,
    Scheme, RoomScheme, FurnitureItem, ConstraintCheck,
    GridPlan, GridRoom,
)

# 1x1 像素 PNG，占位图
_PNG_1PX = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


class FakeProvider:
    """返回固定结构化数据，供测试与无密钥演示。"""

    def recognize_floorplan(self, image_bytes: bytes, hint: dict) -> FloorPlan:
        return FloorPlan(
            community=hint.get("community", ""),
            layout_type="三室两厅",
            total_area=89.0,
            rooms=[
                Room(room_id="living_room", name="客厅", area=22.5,
                     polygon=[(0, 0), (5, 0), (5, 4.5), (0, 4.5)]),
                Room(room_id="master_bedroom", name="主卧", area=15.0,
                     polygon=[(5, 0), (9, 0), (9, 3.75), (5, 3.75)]),
            ],
            doors=[Door(room_a="living_room", room_b=None, pos=(0, 2.0)),
                   Door(room_a="living_room", room_b="master_bedroom", pos=(5, 2.0))],
            windows=[Window(room_id="living_room", pos=(2.5, 4.5)),
                     Window(room_id="master_bedroom", pos=(7.0, 0))],
        )

    def extract_grid(self, image_bytes: bytes) -> GridPlan:
        return GridPlan(
            top_dims=[4150, 2900, 3000], bottom_dims=[4150, 1700, 4200],
            left_dims=[1500, 7100, 3000], right_dims=[1500, 5050, 3850, 1200],
            rooms=[
                GridRoom(name="客餐厅", area=31.03, bbox=[0.05, 0.3, 0.45, 0.75]),
                GridRoom(name="主卧", area=13.63, bbox=[0.55, 0.6, 0.95, 0.9]),
            ])

    def parse_requirement(self, options: dict, transcript: str) -> Requirement:
        constraints = []
        if "不拆承重墙" in transcript:
            constraints.append("不拆承重墙")
        preferences = []
        if "书房" in transcript or "书房" in str(options.get("preferences", "")):
            preferences.append("要书房")
        return Requirement(
            style=options.get("style", ""),
            budget_level=options.get("budget_level", "中"),
            household=options.get("household", ""),
            constraints=constraints,
            preferences=preferences,
        )

    def generate_scheme(self, floorplan: FloorPlan, requirement: Requirement) -> Scheme:
        rooms = []
        for r in floorplan.rooms:
            furniture = [FurnitureItem(item="占位家具", pos=(r.polygon[0][0] + 0.5,
                                                         r.polygon[0][1] + 0.5),
                                       facing="北", size=(1.0, 1.0))]
            rooms.append(RoomScheme(
                room_id=r.room_id, name=r.name, furniture=furniture,
                finishes={"地面": "浅色木地板"}, soft=["落地灯"],
                render_prompt=f"{requirement.style or '现代'}风格{r.name}, 温暖自然光",
            ))
        return Scheme(
            scheme_id="fake-scheme", floorplan_ref="fake-fp",
            style=requirement.style, palette=["米白", "浅木"],
            budget_level=requirement.budget_level, rooms=rooms,
            constraints_check=[ConstraintCheck(rule=c, status="pass")
                               for c in requirement.constraints],
        )

    def render_perspective(self, prompt: str, reference_svg: str) -> bytes:
        return _PNG_1PX
