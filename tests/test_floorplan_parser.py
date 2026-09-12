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
