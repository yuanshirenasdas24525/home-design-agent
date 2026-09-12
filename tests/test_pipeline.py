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
