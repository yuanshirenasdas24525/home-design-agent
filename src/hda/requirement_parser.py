# src/hda/requirement_parser.py
from __future__ import annotations
from hda.models import Requirement
from hda.providers.base import LLMProvider


def parse_requirement(llm: LLMProvider, options: dict, transcript: str = "") -> Requirement:
    """② 需求解析：选项框为准，口述补充；硬约束由 Provider 抽取。

    冲突时以 options 为准 —— 这里通过'把 options 作为权威字段传入'实现，
    FakeProvider/真实 Provider 均遵循此约定。
    """
    return llm.parse_requirement(options=options, transcript=transcript)
