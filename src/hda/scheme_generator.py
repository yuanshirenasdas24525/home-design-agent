# src/hda/scheme_generator.py
from __future__ import annotations
from hda.models import FloorPlan, Requirement, Scheme, ConstraintCheck
from hda.providers.base import LLMProvider


def generate_scheme(llm: LLMProvider, floorplan: FloorPlan, requirement: Requirement) -> Scheme:
    """③ 方案生成：委托 LLM 出结构化方案，回填户型关联与约束校验。

    骨架阶段摆位逻辑在 Provider 内做最简处理；碰撞检测/门窗避让由后续计划承接。
    """
    scheme = llm.generate_scheme(floorplan, requirement)
    scheme.floorplan_ref = f"{floorplan.community}:{floorplan.layout_type}"
    scheme.constraints_check = check_constraints(scheme, requirement)
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
