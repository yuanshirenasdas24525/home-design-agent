from __future__ import annotations
from typing import Protocol
from hda.models import FloorPlan, Requirement, Scheme


class VisionProvider(Protocol):
    def recognize_floorplan(self, image_bytes: bytes, hint: dict) -> FloorPlan: ...


class LLMProvider(Protocol):
    def parse_requirement(self, options: dict, transcript: str) -> Requirement: ...
    def generate_scheme(self, floorplan: FloorPlan, requirement: Requirement) -> Scheme: ...


class ImageProvider(Protocol):
    def render_perspective(self, prompt: str, reference_svg: str) -> bytes: ...


class Provider(VisionProvider, LLMProvider, ImageProvider, Protocol):
    """三合一 Provider，方便注入。真实实现可分开组合。"""
