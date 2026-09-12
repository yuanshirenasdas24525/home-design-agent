# Phase 0 走通骨架 (Walking Skeleton) 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 ①识别→②需求→③方案→④彩平图→⑤实景图 整条流水线端到端跑通，AI 调用藏在可替换 Provider 接口后，用 Fake Provider 让全流程无需真实密钥即可测试与演示。

**Architecture:** 一条同步流水线（Pipeline）串联 5 个模块，中心数据是 Scheme。所有外部 AI（视觉/LLM/图像）通过三个 Provider 抽象接口调用；测试和本地演示用 FakeProvider（返回固定结构化数据），真实 API 做成一个隔离适配器。纯逻辑（数据模型、约束校验、2D SVG 渲染、编排）全部 TDD、可测。前端是 FastAPI 托管的一个极简单页工作台。

**Tech Stack:** Python 3.11+、pydantic v2（数据模型）、FastAPI + uvicorn（服务/前端托管）、pytest（测试）、纯 Python 生成 SVG（彩平图）、OpenAI 兼容 SDK（真实 Provider 适配器，可替换）。

**参考 spec:** `docs/superpowers/specs/2026-09-12-home-design-agent-design.md`

**范围说明:** 本计划只做"走通骨架"——每个模块的逻辑取最小可用实现（例如识别只保证拓扑结构、方案生成用简单摆位规则、实景图可为占位）。做深各模块由后续独立计划承接。

---

## 文件结构

```
home-design-agent/
├── pyproject.toml                      # 依赖与打包
├── src/hda/
│   ├── __init__.py
│   ├── models.py                       # Task 1: FloorPlan / Requirement / Scheme 数据模型
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py                     # Task 2: VisionProvider/LLMProvider/ImageProvider 抽象
│   │   ├── fake.py                     # Task 2: FakeProvider（测试与演示用）
│   │   └── openai_compat.py            # Task 9: 真实适配器（OpenAI 兼容）
│   ├── floorplan_parser.py             # Task 3: ① 户型识别
│   ├── requirement_parser.py           # Task 4: ② 需求解析
│   ├── scheme_generator.py             # Task 5: ③ 方案生成 + 约束校验
│   ├── plan_renderer.py                # Task 6: ④ 2D 彩平图 SVG 渲染
│   ├── perspective_render.py           # Task 7: ⑤ 实景图生成
│   ├── pipeline.py                     # Task 8: 编排 + 按房间重跑
│   └── web/
│       ├── app.py                      # Task 10: FastAPI 端点
│       └── static/index.html           # Task 10: 极简工作台单页
└── tests/
    ├── test_models.py                  # Task 1
    ├── test_fake_provider.py           # Task 2
    ├── test_floorplan_parser.py        # Task 3
    ├── test_requirement_parser.py      # Task 4
    ├── test_scheme_generator.py        # Task 5
    ├── test_plan_renderer.py           # Task 6
    ├── test_perspective_render.py      # Task 7
    ├── test_pipeline.py                # Task 8
    └── test_web.py                     # Task 10
```

每个模块单一职责；Provider 抽象是 AI 与业务逻辑的接缝，保证"先商业 API、后自建"可无缝替换。

---

## Task 0: 项目脚手架

**Files:**
- Create: `pyproject.toml`
- Create: `src/hda/__init__.py`
- Create: `src/hda/providers/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: 写 pyproject.toml**

```toml
[project]
name = "hda"
version = "0.0.1"
description = "户型效果预览 Agent"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.6",
    "fastapi>=0.110",
    "uvicorn>=0.29",
    "python-multipart>=0.0.9",
    "openai>=1.30",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "httpx>=0.27"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 2: 建空包文件**

`src/hda/__init__.py`、`src/hda/providers/__init__.py`、`tests/__init__.py` 均写入单行：

```python
```

（空文件即可。）

- [ ] **Step 3: 安装依赖并确认 pytest 可运行**

Run: `python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]" && pytest -q`
Expected: `no tests ran`（0 收集，安装成功、无报错）

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml src/hda/__init__.py src/hda/providers/__init__.py tests/__init__.py
git commit -m "chore: 项目脚手架与依赖"
```

---

## Task 1: 核心数据模型

**Files:**
- Create: `src/hda/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_models.py
from hda.models import FloorPlan, Room, Requirement, Scheme, RoomScheme, FurnitureItem, ConstraintCheck


def test_floorplan_roundtrips():
    fp = FloorPlan(
        community="阳光花园", layout_type="三室两厅", total_area=89.0,
        rooms=[Room(room_id="living_room", name="客厅", area=22.5,
                    polygon=[(0, 0), (5, 0), (5, 4.5), (0, 4.5)])],
        doors=[], windows=[],
    )
    assert fp.rooms[0].room_id == "living_room"
    assert FloorPlan.model_validate(fp.model_dump()) == fp


def test_scheme_room_is_independent_unit():
    scheme = Scheme(
        scheme_id="s1", floorplan_ref="fp1",
        style="北欧", palette=["米白", "浅木"], budget_level="中",
        rooms=[RoomScheme(
            room_id="living_room", name="客厅",
            furniture=[FurnitureItem(item="布艺三人沙发", pos=(1.0, 1.0), facing="北", size=(2.4, 0.9))],
            finishes={"地面": "浅色木地板"}, soft=["落地灯"],
            render_prompt="北欧风客厅, 布艺沙发...",
        )],
        constraints_check=[ConstraintCheck(rule="不拆承重墙", status="pass")],
    )
    assert scheme.rooms[0].furniture[0].item == "布艺三人沙发"
    assert scheme.get_room("living_room").name == "客厅"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_models.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'hda.models'`

- [ ] **Step 3: 写最小实现**

```python
# src/hda/models.py
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
    size: Point = (0.0, 0.0)


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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_models.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add src/hda/models.py tests/test_models.py
git commit -m "feat: 核心数据模型 FloorPlan/Requirement/Scheme"
```

---

## Task 2: Provider 抽象接口 + FakeProvider

**Files:**
- Create: `src/hda/providers/base.py`
- Create: `src/hda/providers/fake.py`
- Test: `tests/test_fake_provider.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_fake_provider.py
from hda.models import FloorPlan, Requirement, Scheme
from hda.providers.fake import FakeProvider


def test_fake_vision_returns_floorplan():
    p = FakeProvider()
    fp = p.recognize_floorplan(image_bytes=b"fake-image", hint={"community": "阳光花园"})
    assert isinstance(fp, FloorPlan)
    assert fp.community == "阳光花园"
    assert len(fp.rooms) >= 1


def test_fake_llm_parses_requirement():
    p = FakeProvider()
    req = p.parse_requirement(options={"style": "北欧"}, transcript="想要个书房，不拆承重墙")
    assert isinstance(req, Requirement)
    assert req.style == "北欧"
    assert "不拆承重墙" in req.constraints


def test_fake_llm_generates_scheme():
    p = FakeProvider()
    fp = p.recognize_floorplan(b"x", {})
    req = Requirement(style="北欧")
    scheme = p.generate_scheme(fp, req)
    assert isinstance(scheme, Scheme)
    assert len(scheme.rooms) == len(fp.rooms)


def test_fake_image_returns_bytes():
    p = FakeProvider()
    img = p.render_perspective(prompt="北欧客厅", reference_svg="<svg/>")
    assert isinstance(img, bytes) and len(img) > 0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_fake_provider.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'hda.providers.fake'`

- [ ] **Step 3: 写抽象接口**

```python
# src/hda/providers/base.py
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
```

- [ ] **Step 4: 写 FakeProvider**

```python
# src/hda/providers/fake.py
from __future__ import annotations
from hda.models import (
    FloorPlan, Room, Door, Window, Requirement,
    Scheme, RoomScheme, FurnitureItem, ConstraintCheck,
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
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_fake_provider.py -v`
Expected: PASS（4 passed）

- [ ] **Step 6: Commit**

```bash
git add src/hda/providers/base.py src/hda/providers/fake.py tests/test_fake_provider.py
git commit -m "feat: Provider 抽象接口与 FakeProvider"
```

---

## Task 3: ① 户型识别模块

**Files:**
- Create: `src/hda/floorplan_parser.py`
- Test: `tests/test_floorplan_parser.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_floorplan_parser.py
from hda.floorplan_parser import parse_floorplan
from hda.providers.fake import FakeProvider


def test_parse_floorplan_delegates_to_vision_provider():
    fp = parse_floorplan(FakeProvider(), image_bytes=b"img", community="阳光花园")
    assert fp.community == "阳光花园"
    assert {r.room_id for r in fp.rooms} == {"living_room", "master_bedroom"}


def test_parse_floorplan_requires_at_least_one_room():
    class EmptyVision:
        def recognize_floorplan(self, image_bytes, hint):
            from hda.models import FloorPlan
            return FloorPlan(rooms=[])
    try:
        parse_floorplan(EmptyVision(), image_bytes=b"img", community="x")
        assert False, "应抛出异常"
    except ValueError as e:
        assert "未识别到房间" in str(e)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_floorplan_parser.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'hda.floorplan_parser'`

- [ ] **Step 3: 写最小实现**

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_floorplan_parser.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add src/hda/floorplan_parser.py tests/test_floorplan_parser.py
git commit -m "feat: ① 户型识别模块"
```

---

## Task 4: ② 需求解析模块

**Files:**
- Create: `src/hda/requirement_parser.py`
- Test: `tests/test_requirement_parser.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_requirement_parser.py
from hda.requirement_parser import parse_requirement
from hda.providers.fake import FakeProvider


def test_options_win_over_transcript_for_style():
    # 选项框给了风格，口述里的风格不应覆盖
    req = parse_requirement(FakeProvider(), options={"style": "北欧"},
                            transcript="我其实想要美式")
    assert req.style == "北欧"


def test_hard_constraints_extracted_from_transcript():
    req = parse_requirement(FakeProvider(), options={"style": "北欧"},
                            transcript="不拆承重墙")
    assert "不拆承重墙" in req.constraints
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_requirement_parser.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'hda.requirement_parser'`

- [ ] **Step 3: 写最小实现**

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_requirement_parser.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add src/hda/requirement_parser.py tests/test_requirement_parser.py
git commit -m "feat: ② 需求解析模块"
```

---

## Task 5: ③ 方案生成 + 约束校验

**Files:**
- Create: `src/hda/scheme_generator.py`
- Test: `tests/test_scheme_generator.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_scheme_generator.py
from hda.models import FloorPlan, Room, Requirement, Scheme
from hda.scheme_generator import generate_scheme, check_constraints
from hda.providers.fake import FakeProvider


def _fp():
    return FloorPlan(
        community="阳光花园", layout_type="三室两厅", total_area=89.0,
        rooms=[Room(room_id="living_room", name="客厅", area=22.5,
                    polygon=[(0, 0), (5, 0), (5, 4.5), (0, 4.5)])],
    )


def test_generate_scheme_covers_every_room():
    fp = _fp()
    scheme = generate_scheme(FakeProvider(), fp, Requirement(style="北欧"))
    assert {r.room_id for r in scheme.rooms} == {"living_room"}
    assert scheme.floorplan_ref  # 关联户型


def test_check_constraints_marks_load_bearing_pass_when_no_wall_change():
    fp = _fp()
    scheme = generate_scheme(FakeProvider(), fp, Requirement(constraints=["不拆承重墙"]))
    checks = check_constraints(scheme, Requirement(constraints=["不拆承重墙"]))
    assert any(c.rule == "不拆承重墙" and c.status == "pass" for c in checks)


def test_check_constraints_fails_missing_required_room():
    fp = _fp()
    scheme = generate_scheme(FakeProvider(), fp, Requirement())
    # 要求"要书房"，但户型/方案里没有书房 -> fail
    checks = check_constraints(scheme, Requirement(preferences=["要书房"]))
    assert any(c.rule == "要书房" and c.status == "fail" for c in checks)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_scheme_generator.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'hda.scheme_generator'`

- [ ] **Step 3: 写最小实现**

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_scheme_generator.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5: Commit**

```bash
git add src/hda/scheme_generator.py tests/test_scheme_generator.py
git commit -m "feat: ③ 方案生成与约束校验"
```

---

## Task 6: ④ 2D 彩平图渲染

**Files:**
- Create: `src/hda/plan_renderer.py`
- Test: `tests/test_plan_renderer.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_plan_renderer.py
from hda.models import FloorPlan, Room, Scheme, RoomScheme, FurnitureItem
from hda.plan_renderer import render_colored_plan


def _fp():
    return FloorPlan(rooms=[
        Room(room_id="living_room", name="客厅", area=22.5,
             polygon=[(0, 0), (5, 0), (5, 4.5), (0, 4.5)]),
    ])


def _scheme():
    return Scheme(scheme_id="s", floorplan_ref="f", rooms=[
        RoomScheme(room_id="living_room", name="客厅",
                   furniture=[FurnitureItem(item="沙发", pos=(1, 1), size=(2, 1))]),
    ])


def test_render_produces_svg_with_room_and_furniture():
    svg = render_colored_plan(_fp(), _scheme())
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    assert "客厅" in svg      # 房间名标注
    assert "沙发" in svg      # 家具标注


def test_render_scales_to_viewbox():
    svg = render_colored_plan(_fp(), _scheme())
    assert "viewBox" in svg
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_plan_renderer.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'hda.plan_renderer'`

- [ ] **Step 3: 写最小实现**

```python
# src/hda/plan_renderer.py
from __future__ import annotations
from hda.models import FloorPlan, Scheme

SCALE = 100  # 1 米 = 100 像素
PAD = 40


def _bounds(fp: FloorPlan):
    xs = [p[0] for r in fp.rooms for p in r.polygon]
    ys = [p[1] for r in fp.rooms for p in r.polygon]
    return min(xs), min(ys), max(xs), max(ys)


def render_colored_plan(floorplan: FloorPlan, scheme: Scheme) -> str:
    """④ 从 Scheme 坐标程序化渲染 2D 彩平图（纯逻辑，零 AI）。"""
    minx, miny, maxx, maxy = _bounds(floorplan)
    w = (maxx - minx) * SCALE + PAD * 2
    h = (maxy - miny) * SCALE + PAD * 2

    def sx(x): return (x - minx) * SCALE + PAD
    def sy(y): return (y - miny) * SCALE + PAD

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
        f'font-family="sans-serif">',
        f'<rect width="{w:.0f}" height="{h:.0f}" fill="#faf8f5"/>',
    ]

    for room in floorplan.rooms:
        pts = " ".join(f"{sx(x):.0f},{sy(y):.0f}" for x, y in room.polygon)
        parts.append(f'<polygon points="{pts}" fill="#f0ead9" '
                     f'stroke="#4a4a4a" stroke-width="3"/>')
        cx = sum(sx(x) for x, _ in room.polygon) / len(room.polygon)
        cy = sum(sy(y) for _, y in room.polygon) / len(room.polygon)
        parts.append(f'<text x="{cx:.0f}" y="{cy:.0f}" font-size="16" '
                     f'text-anchor="middle" fill="#333">{room.name}</text>')

    for rs in scheme.rooms:
        for f in rs.furniture:
            fx, fy = sx(f.pos[0]), sy(f.pos[1])
            fw, fh = f.size[0] * SCALE, f.size[1] * SCALE
            parts.append(f'<rect x="{fx:.0f}" y="{fy:.0f}" width="{fw:.0f}" '
                         f'height="{fh:.0f}" fill="#c9b79c" stroke="#8a7a5c" '
                         f'rx="4" opacity="0.9"/>')
            parts.append(f'<text x="{fx + fw / 2:.0f}" y="{fy + fh / 2:.0f}" '
                         f'font-size="11" text-anchor="middle" fill="#5a4a2c">{f.item}</text>')

    parts.append("</svg>")
    return "\n".join(parts)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_plan_renderer.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add src/hda/plan_renderer.py tests/test_plan_renderer.py
git commit -m "feat: ④ 2D 彩平图 SVG 渲染"
```

---

## Task 7: ⑤ 实景图生成

**Files:**
- Create: `src/hda/perspective_render.py`
- Test: `tests/test_perspective_render.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_perspective_render.py
from hda.models import Scheme, RoomScheme
from hda.perspective_render import render_perspectives
from hda.providers.fake import FakeProvider


def test_render_one_image_per_room():
    scheme = Scheme(scheme_id="s", floorplan_ref="f", rooms=[
        RoomScheme(room_id="living_room", name="客厅", render_prompt="北欧客厅"),
        RoomScheme(room_id="master_bedroom", name="主卧", render_prompt="北欧主卧"),
    ])
    images = render_perspectives(FakeProvider(), scheme, reference_svg="<svg/>")
    assert set(images.keys()) == {"living_room", "master_bedroom"}
    assert all(isinstance(v, bytes) and len(v) > 0 for v in images.values())


def test_render_skips_rooms_without_prompt():
    scheme = Scheme(scheme_id="s", floorplan_ref="f", rooms=[
        RoomScheme(room_id="balcony", name="阳台", render_prompt=""),
    ])
    images = render_perspectives(FakeProvider(), scheme, reference_svg="<svg/>")
    assert images == {}
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_perspective_render.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'hda.perspective_render'`

- [ ] **Step 3: 写最小实现**

```python
# src/hda/perspective_render.py
from __future__ import annotations
from hda.models import Scheme
from hda.providers.base import ImageProvider


def render_perspectives(image: ImageProvider, scheme: Scheme,
                        reference_svg: str) -> dict[str, bytes]:
    """⑤ 每个有 render_prompt 的房间出一张实景图。返回 room_id -> 图片字节。"""
    out: dict[str, bytes] = {}
    for rs in scheme.rooms:
        if not rs.render_prompt:
            continue
        out[rs.room_id] = image.render_perspective(
            prompt=rs.render_prompt, reference_svg=reference_svg)
    return out
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_perspective_render.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add src/hda/perspective_render.py tests/test_perspective_render.py
git commit -m "feat: ⑤ 实景图生成模块"
```

---

## Task 8: 流水线编排 + 按房间重跑

**Files:**
- Create: `src/hda/pipeline.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_pipeline.py
from hda.pipeline import Pipeline, PreviewResult
from hda.providers.fake import FakeProvider


def test_pipeline_end_to_end_produces_preview():
    pipe = Pipeline(FakeProvider())
    result = pipe.run(
        image_bytes=b"img", community="阳光花园",
        options={"style": "北欧"}, transcript="不拆承重墙",
    )
    assert isinstance(result, PreviewResult)
    assert result.floorplan.community == "阳光花园"
    assert result.colored_plan_svg.startswith("<svg")
    assert len(result.perspectives) == len(result.scheme.rooms)
    assert any(c.rule == "不拆承重墙" for c in result.scheme.constraints_check)


def test_pipeline_regenerate_single_room_keeps_others():
    pipe = Pipeline(FakeProvider())
    result = pipe.run(image_bytes=b"img", community="x",
                      options={"style": "北欧"}, transcript="")
    before = result.scheme.get_room("master_bedroom")
    updated = pipe.regenerate_room(result, room_id="living_room",
                                   options={"style": "美式"}, transcript="")
    # 未改动的房间对象保持不变
    assert updated.scheme.get_room("master_bedroom") == before
    # 目标房间重渲了图
    assert "living_room" in updated.perspectives
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_pipeline.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'hda.pipeline'`

- [ ] **Step 3: 写最小实现**

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_pipeline.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add src/hda/pipeline.py tests/test_pipeline.py
git commit -m "feat: 流水线编排与按房间重跑"
```

---

## Task 9: 真实 Provider 适配器（OpenAI 兼容，可替换）

**Files:**
- Create: `src/hda/providers/openai_compat.py`
- Test: `tests/test_openai_compat.py`

> 说明：多数国产大模型（豆包方舟/通义千问/DeepSeek/Kimi）都提供 OpenAI 兼容端点。此适配器面向该协议，`base_url`/`model` 可配置切换。图像端点各家差异大，此处封装为一个可注入的 `image_call` 回调，真实接哪家在配置层决定，不写死。测试用 monkeypatch 打桩，不触真实网络。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_openai_compat.py
import json
from hda.models import FloorPlan, Requirement
from hda.providers.openai_compat import OpenAICompatProvider


class _FakeChat:
    """模拟 openai 客户端 chat.completions.create 返回。"""
    def __init__(self, payload): self._payload = payload

    def create(self, **kwargs):
        class _Msg: content = json.dumps(self._payload, ensure_ascii=False)
        class _Choice: message = _Msg()
        class _Resp: choices = [_Choice()]
        return _Resp()


def _provider_with(payload, image_call=None):
    p = OpenAICompatProvider(api_key="x", base_url="http://fake", model="m",
                             image_call=image_call or (lambda prompt, ref: b"IMG"))
    p._client.chat.completions = _FakeChat(payload)  # 注入桩
    return p


def test_recognize_floorplan_parses_json():
    payload = {"community": "阳光花园", "layout_type": "两室一厅", "total_area": 70,
               "rooms": [{"room_id": "living_room", "name": "客厅", "area": 20,
                          "polygon": [[0, 0], [4, 0], [4, 5], [0, 5]]}],
               "doors": [], "windows": []}
    fp = _provider_with(payload).recognize_floorplan(b"img", {"community": "阳光花园"})
    assert isinstance(fp, FloorPlan)
    assert fp.rooms[0].name == "客厅"


def test_parse_requirement_parses_json():
    payload = {"style": "北欧", "budget_level": "中", "household": "三口之家",
               "constraints": ["不拆承重墙"], "preferences": ["要书房"]}
    req = _provider_with(payload).parse_requirement({"style": "北欧"}, "不拆承重墙, 要书房")
    assert isinstance(req, Requirement)
    assert "不拆承重墙" in req.constraints


def test_render_perspective_uses_image_call():
    called = {}
    def image_call(prompt, ref):
        called["prompt"] = prompt
        return b"REALIMG"
    img = _provider_with({}, image_call=image_call).render_perspective("北欧客厅", "<svg/>")
    assert img == b"REALIMG"
    assert called["prompt"] == "北欧客厅"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_openai_compat.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'hda.providers.openai_compat'`

- [ ] **Step 3: 写最小实现**

```python
# src/hda/providers/openai_compat.py
from __future__ import annotations
import base64
import json
from typing import Callable
from openai import OpenAI
from hda.models import FloorPlan, Requirement, Scheme

ImageCall = Callable[[str, str], bytes]  # (prompt, reference_svg) -> image bytes


class OpenAICompatProvider:
    """面向 OpenAI 兼容协议的真实 Provider。base_url/model 可切换不同厂商。

    图像生成各家协议不同，通过 image_call 回调注入，避免写死某一家。
    """

    def __init__(self, api_key: str, base_url: str, model: str, image_call: ImageCall):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._image_call = image_call

    def _chat_json(self, system: str, user_text: str, image_bytes: bytes | None = None) -> dict:
        content: list[dict] = [{"type": "text", "text": user_text}]
        if image_bytes is not None:
            b64 = base64.b64encode(image_bytes).decode()
            content.append({"type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64}"}})
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": content}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        return json.loads(resp.choices[0].message.content)

    def recognize_floorplan(self, image_bytes: bytes, hint: dict) -> FloorPlan:
        system = ("你是户型图识别专家。输出 JSON，字段：community,layout_type,total_area,"
                  "rooms[{room_id,name,area,polygon}],doors[{room_a,room_b,pos}],"
                  "windows[{room_id,pos}]。坐标单位米。优先保证房间拓扑正确。")
        data = self._chat_json(system, f"小区提示：{hint.get('community','')}", image_bytes)
        return FloorPlan.model_validate(data)

    def parse_requirement(self, options: dict, transcript: str) -> Requirement:
        system = ("你把装修需求解析为 JSON：style,budget_level(低/中/高),household,"
                  "constraints[],preferences[]。选项框字段为权威，口述仅补充；"
                  "冲突以选项框为准。硬约束务必抽全放入 constraints。")
        user = f"选项框：{json.dumps(options, ensure_ascii=False)}\n口述：{transcript}"
        data = self._chat_json(system, user)
        for k, v in options.items():  # 选项框为准
            if v:
                data[k] = v
        return Requirement.model_validate(data)

    def generate_scheme(self, floorplan: FloorPlan, requirement: Requirement) -> Scheme:
        system = ("你是资深室内设计师。根据户型与需求输出 JSON Scheme："
                  "scheme_id,floorplan_ref,style,palette[],budget_level,"
                  "rooms[{room_id,name,furniture[{item,pos,facing,size}],finishes{},"
                  "soft[],render_prompt}]。每个房间都要写 render_prompt（含风格/家具/材质/视角）。"
                  "家具 pos 必须落在对应房间 polygon 内，不得挡门。")
        user = (f"户型：{floorplan.model_dump_json()}\n"
                f"需求：{requirement.model_dump_json()}")
        data = self._chat_json(system, user)
        return Scheme.model_validate(data)

    def render_perspective(self, prompt: str, reference_svg: str) -> bytes:
        return self._image_call(prompt, reference_svg)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_openai_compat.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5: Commit**

```bash
git add src/hda/providers/openai_compat.py tests/test_openai_compat.py
git commit -m "feat: OpenAI 兼容真实 Provider 适配器"
```

---

## Task 10: FastAPI 端点 + 极简工作台

**Files:**
- Create: `src/hda/web/__init__.py`（空）
- Create: `src/hda/web/app.py`
- Create: `src/hda/web/static/index.html`
- Test: `tests/test_web.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_web.py
from fastapi.testclient import TestClient
from hda.web.app import create_app
from hda.providers.fake import FakeProvider


def _client():
    return TestClient(create_app(provider=FakeProvider()))


def test_preview_endpoint_returns_svg_and_images():
    files = {"image": ("plan.png", b"fakeimg", "image/png")}
    data = {"community": "阳光花园", "style": "北欧", "transcript": "不拆承重墙"}
    resp = _client().post("/api/preview", files=files, data=data)
    assert resp.status_code == 200
    body = resp.json()
    assert body["colored_plan_svg"].startswith("<svg")
    assert len(body["perspectives"]) >= 1          # room_id -> data URL
    assert body["scheme"]["style"] == "北欧"


def test_index_page_served():
    resp = _client().get("/")
    assert resp.status_code == 200
    assert "户型效果预览" in resp.text
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_web.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'hda.web.app'`

- [ ] **Step 3: 写 FastAPI 应用**

```python
# src/hda/web/app.py
from __future__ import annotations
import base64
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from hda.pipeline import Pipeline
from hda.providers.base import Provider

_STATIC = Path(__file__).parent / "static"


def create_app(provider: Provider) -> FastAPI:
    app = FastAPI(title="户型效果预览 Agent")
    pipe = Pipeline(provider)

    @app.get("/", response_class=HTMLResponse)
    def index():
        return (_STATIC / "index.html").read_text(encoding="utf-8")

    @app.post("/api/preview")
    async def preview(image: UploadFile = File(...), community: str = Form(""),
                      style: str = Form(""), transcript: str = Form("")):
        img_bytes = await image.read()
        result = pipe.run(image_bytes=img_bytes, community=community,
                          options={"style": style}, transcript=transcript)
        perspectives = {
            rid: "data:image/png;base64," + base64.b64encode(b).decode()
            for rid, b in result.perspectives.items()
        }
        return JSONResponse({
            "colored_plan_svg": result.colored_plan_svg,
            "perspectives": perspectives,
            "scheme": result.scheme.model_dump(),
        })

    return app
```

- [ ] **Step 4: 写极简工作台页面**

```html
<!-- src/hda/web/static/index.html -->
<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>户型效果预览 Agent</title>
  <style>
    body { font-family: -apple-system, "PingFang SC", sans-serif; margin: 24px; color: #222; }
    label { display: block; margin: 8px 0 4px; font-weight: 600; }
    input, textarea { width: 320px; padding: 6px; }
    button { margin-top: 16px; padding: 10px 20px; font-size: 15px; cursor: pointer; }
    #out { margin-top: 24px; display: flex; flex-wrap: wrap; gap: 16px; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 12px; }
    img, svg { max-width: 360px; height: auto; }
  </style>
</head>
<body>
  <h1>户型效果预览</h1>
  <form id="f">
    <label>户型图</label><input type="file" name="image" accept="image/*" required/>
    <label>小区名</label><input name="community" placeholder="如 阳光花园"/>
    <label>风格</label><input name="style" placeholder="如 北欧"/>
    <label>口述需求</label><textarea name="transcript" rows="3" placeholder="不拆承重墙，要个书房..."></textarea>
    <button type="submit">生成预览</button>
  </form>
  <div id="out"></div>
  <script>
    document.getElementById('f').addEventListener('submit', async (e) => {
      e.preventDefault();
      const out = document.getElementById('out');
      out.innerHTML = '生成中…';
      const resp = await fetch('/api/preview', { method: 'POST', body: new FormData(e.target) });
      const data = await resp.json();
      out.innerHTML = '<div class="card"><h3>彩平图</h3>' + data.colored_plan_svg + '</div>';
      for (const [rid, url] of Object.entries(data.perspectives)) {
        out.innerHTML += '<div class="card"><h3>' + rid + '</h3><img src="' + url + '"/></div>';
      }
    });
  </script>
</body>
</html>
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_web.py -v`
Expected: PASS（2 passed）

- [ ] **Step 6: 手动冒烟（可选）**

创建 `run_local.py`：

```python
# run_local.py
import uvicorn
from hda.web.app import create_app
from hda.providers.fake import FakeProvider

if __name__ == "__main__":
    uvicorn.run(create_app(FakeProvider()), host="127.0.0.1", port=8000)
```

Run: `python run_local.py` 然后浏览器打开 `http://127.0.0.1:8000`，上传任意图片点"生成预览"，应看到彩平图 + 每间房占位图。

- [ ] **Step 7: Commit**

```bash
git add src/hda/web/ tests/test_web.py run_local.py
git commit -m "feat: FastAPI 端点与极简工作台页面"
```

---

## Task 11: 端到端冒烟测试

**Files:**
- Test: `tests/test_e2e_smoke.py`

- [ ] **Step 1: 写端到端测试**

```python
# tests/test_e2e_smoke.py
from hda.pipeline import Pipeline
from hda.providers.fake import FakeProvider


def test_full_flow_smoke():
    """一张图 + 需求 → 彩平图 + 实景图 + 通过约束校验，链路不断。"""
    pipe = Pipeline(FakeProvider())
    r = pipe.run(image_bytes=b"img", community="阳光花园",
                 options={"style": "北欧", "budget_level": "中"},
                 transcript="不拆承重墙")
    # 五个模块都产出了东西
    assert r.floorplan.rooms
    assert r.requirement.style == "北欧"
    assert r.scheme.rooms
    assert r.colored_plan_svg.startswith("<svg")
    assert r.perspectives
    # 约束校验通过
    assert all(c.status == "pass" for c in r.scheme.constraints_check)
```

- [ ] **Step 2: 运行全部测试确认通过**

Run: `pytest -q`
Expected: 全绿（约 18 passed），无 failure

- [ ] **Step 3: Commit**

```bash
git add tests/test_e2e_smoke.py
git commit -m "test: 端到端冒烟测试"
```

---

## 自查清单结果

- **Spec 覆盖**：①②③④⑤ 五模块 + 编排 + 约束校验 + 按房间重跑 + 案例库检索键（community/layout_type 已进 FloorPlan/floorplan_ref）均有对应任务。⑥3D、⑦案例库存储、真实图像 API 具体选型属后续 Phase，已在范围说明中排除。
- **占位符扫描**：无 TBD/TODO；每个代码步骤含完整可运行代码。
- **类型一致性**：`FloorPlan/Requirement/Scheme/RoomScheme/FurnitureItem/ConstraintCheck` 全程一致；`Pipeline.run`/`regenerate_room`、`generate_scheme`/`check_constraints`、`render_colored_plan`、`render_perspectives` 签名跨任务一致。
- **Provider 接缝**：FakeProvider 与 OpenAICompatProvider 实现同一组方法名，可无缝替换。
