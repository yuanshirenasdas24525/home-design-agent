# src/hda/floorplan_parser.py
from __future__ import annotations
from hda.models import FloorPlan
from hda.providers.base import VisionProvider


def parse_floorplan(vision: VisionProvider, image_bytes: bytes, community: str = "") -> FloorPlan:
    """① 户型识别：调用视觉 Provider，做最小有效性校验。

    骨架阶段只保证'至少识别到一个房间'；精确尺寸/人工校验由后续计划承接。
    """
    fp = vision.recognize_floorplan(image_bytes, {"community": community})
    if not fp.rooms:
        raise ValueError("户型识别失败：未识别到房间，请检查图片或人工标注")
    if community and not fp.community:
        fp.community = community
    return fp
