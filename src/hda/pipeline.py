# src/hda/pipeline.py
from __future__ import annotations
from dataclasses import dataclass
from hda.models import FloorPlan, Requirement, Scheme
from hda.providers.base import Provider
from hda.floorplan_parser import parse_floorplan
from hda.requirement_parser import parse_requirement
from hda.scheme_generator import generate_scheme, check_constraints
from hda.plan_renderer import render_colored_plan
from hda.perspective_render import render_perspectives


@dataclass
class PreviewResult:
    floorplan: FloorPlan
    requirement: Requirement
    scheme: Scheme
    colored_plan_svg: str
    perspectives: dict[str, bytes]


class Pipeline:
    """编排 ①→⑤，并支持按房间重跑。"""

    def __init__(self, provider: Provider):
        self.p = provider

    def design_from_floorplan(self, floorplan: FloorPlan,
                              options: dict, transcript: str):
        """从已校正的户型几何出发（跳过①识别）：②需求 → ③方案 → ④带家具彩平图。

        几何已由半自动/描线锁定，家具方案锚定在这份几何上，天然对得上。
        返回 (requirement, scheme, colored_plan_svg)。
        """
        req = parse_requirement(self.p, options, transcript)          # ②
        scheme = generate_scheme(self.p, floorplan, req)              # ③（含家具兜底）
        svg = render_colored_plan(floorplan, scheme)                  # ④
        return req, scheme, svg

    def run(self, image_bytes: bytes, community: str,
            options: dict, transcript: str) -> PreviewResult:
        fp = parse_floorplan(self.p, image_bytes, community)          # ①
        req = parse_requirement(self.p, options, transcript)          # ②
        scheme = generate_scheme(self.p, fp, req)                     # ③
        svg = render_colored_plan(fp, scheme)                         # ④
        images = render_perspectives(self.p, scheme, svg)             # ⑤
        return PreviewResult(fp, req, scheme, svg, images)

    def regenerate_room(self, result: PreviewResult, room_id: str,
                        options: dict, transcript: str) -> PreviewResult:
        """只重生成一个房间：改该房间的 RoomScheme 并重渲其实景图，其余不动。"""
        req = parse_requirement(self.p, options, transcript)
        fresh = generate_scheme(self.p, result.floorplan, req)
        new_room = fresh.get_room(room_id)
        if new_room is None:
            raise ValueError(f"重生成失败：房间 {room_id} 不存在")

        rooms = [new_room if r.room_id == room_id else r for r in result.scheme.rooms]
        result.scheme.rooms = rooms
        result.scheme.constraints_check = check_constraints(result.scheme, req)
        result.colored_plan_svg = render_colored_plan(result.floorplan, result.scheme)
        result.perspectives[room_id] = self.p.render_perspective(
            prompt=new_room.render_prompt, reference_svg=result.colored_plan_svg)
        return result
