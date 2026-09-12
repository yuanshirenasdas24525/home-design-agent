# src/hda/providers/composite.py
from __future__ import annotations
from hda.models import FloorPlan, Requirement, Scheme
from hda.providers.base import VisionProvider, LLMProvider, ImageProvider


class CompositeProvider:
    """把三路能力分别接到不同厂商：视觉/文本/图像各用最合适的一家。

    - vision: 户型识别（需看图）
    - llm: 需求解析 + 方案生成（纯文本推理）
    - image: 实景图生成（文生图）
    """

    def __init__(self, vision: VisionProvider, llm: LLMProvider, image: ImageProvider):
        self._vision = vision
        self._llm = llm
        self._image = image

    def recognize_floorplan(self, image_bytes: bytes, hint: dict) -> FloorPlan:
        return self._vision.recognize_floorplan(image_bytes, hint)

    def parse_requirement(self, options: dict, transcript: str) -> Requirement:
        return self._llm.parse_requirement(options, transcript)

    def generate_scheme(self, floorplan: FloorPlan, requirement: Requirement) -> Scheme:
        return self._llm.generate_scheme(floorplan, requirement)

    def render_perspective(self, prompt: str, reference_svg: str) -> bytes:
        return self._image.render_perspective(prompt, reference_svg)
