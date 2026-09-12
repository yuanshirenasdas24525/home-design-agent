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
