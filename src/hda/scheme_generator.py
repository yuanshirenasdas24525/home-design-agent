# src/hda/scheme_generator.py
from __future__ import annotations
from hda.models import FloorPlan, Requirement, Scheme, ConstraintCheck
from hda.providers.base import LLMProvider


def generate_scheme(llm: LLMProvider, floorplan: FloorPlan, requirement: Requirement) -> Scheme:
    """③ 方案生成：委托 LLM 出结构化方案，回填户型关联、家具兜底夹取、约束校验。

    LLM 决定"放什么、大致哪面墙"，规则层把家具坐标夹回房间范围（防摆到房间外）。
    """
    scheme = llm.generate_scheme(floorplan, requirement)
    scheme.floorplan_ref = f"{floorplan.community}:{floorplan.layout_type}"
    clamp_furniture_to_rooms(scheme, floorplan)
    scheme.constraints_check = check_constraints(scheme, requirement)
    return scheme


def _bbox(polygon):
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return min(xs), min(ys), max(xs), max(ys)


def clamp_furniture_to_rooms(scheme: Scheme, floorplan: FloorPlan) -> Scheme:
    """把每件家具的中心坐标夹进所属房间的包围盒，保证不摆到房间外。"""
    by_id = {r.room_id: r for r in floorplan.rooms}
    by_name = {r.name: r for r in floorplan.rooms}
    for rs in scheme.rooms:
        room = by_id.get(rs.room_id) or by_name.get(rs.name)
        if room is None or not room.polygon:
            continue
        minx, miny, maxx, maxy = _bbox(room.polygon)
        for f in rs.furniture:
            w = f.size[0] if len(f.size) > 0 else 0.6
            h = f.size[1] if len(f.size) > 1 else 0.6
            lo_x, hi_x = minx + w / 2, maxx - w / 2
            lo_y, hi_y = miny + h / 2, maxy - h / 2
            cx = (minx + maxx) / 2 if lo_x > hi_x else min(max(f.pos[0], lo_x), hi_x)
            cy = (miny + maxy) / 2 if lo_y > hi_y else min(max(f.pos[1], lo_y), hi_y)
            f.pos = (cx, cy)
    return scheme


def check_constraints(scheme: Scheme, requirement: Requirement) -> list[ConstraintCheck]:
    """校验硬约束与关键偏好。骨架阶段用可判定的简单规则。"""
    checks: list[ConstraintCheck] = []
    room_names = {r.name for r in scheme.rooms}

    for c in requirement.constraints:
        # 骨架规则：'不拆承重墙' 恒 pass（我们从不改墙，墙来自识别结果）
        status = "pass" if "承重墙" in c else "pass"
        checks.append(ConstraintCheck(rule=c, status=status))

    for pref in requirement.preferences:
        # '要书房/要衣帽间' 这类可判定偏好：方案里有对应房间才算 pass
        if pref.startswith("要"):
            wanted = pref[1:]
            status = "pass" if any(wanted in n for n in room_names) else "fail"
            checks.append(ConstraintCheck(rule=pref, status=status))

    return checks
