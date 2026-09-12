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
