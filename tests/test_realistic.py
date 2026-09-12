from fastapi.testclient import TestClient
from hda.models import FloorPlan, Room, Scheme, RoomScheme, FurnitureItem
from hda.realistic import render_room_realistic
from hda.web.app import create_app
from hda.providers.fake import FakeProvider


class FakeWanx:
    def doodle(self, sketch_png: bytes, prompt: str) -> bytes:
        assert isinstance(sketch_png, bytes) and len(sketch_png) > 0  # 真栅格化过
        return b"IMG:" + prompt.encode()


def _fp():
    return FloorPlan(
        windows=[],
        rooms=[Room(room_id="living", name="客厅", area=20,
                    polygon=[(0, 0), (5, 0), (5, 4), (0, 4)]),
               Room(room_id="bal", name="阳台A", area=5,
                    polygon=[(0, 4), (5, 4), (5, 5.5), (0, 5.5)])])


def _scheme():
    return Scheme(scheme_id="s", floorplan_ref="f", rooms=[
        RoomScheme(room_id="living", name="客厅",
                   furniture=[FurnitureItem(item="沙发", pos=(1.5, 1.0), size=[2, 0.9])]),
        RoomScheme(room_id="bal", name="阳台A",
                   furniture=[FurnitureItem(item="洗衣机", pos=(1, 4.7), size=[0.6, 0.6])])])


def test_render_room_realistic_skips_balcony():
    imgs = render_room_realistic(_fp(), _scheme(), FakeWanx(), style="北欧")
    assert "living" in imgs and "bal" not in imgs   # 阳台被跳过
    assert imgs["living"].startswith(b"IMG:")


def test_realistic_endpoint_503_without_wanx():
    cli = TestClient(create_app(provider=FakeProvider()))
    body = {"floorplan": _fp().model_dump(), "scheme": _scheme().model_dump()}
    assert cli.post("/api/render_realistic", json=body).status_code == 503


def test_realistic_endpoint_ok_with_wanx():
    cli = TestClient(create_app(provider=FakeProvider(), wanx=FakeWanx()))
    body = {"floorplan": _fp().model_dump(), "scheme": _scheme().model_dump(),
            "style": "北欧", "room_ids": ["living"]}
    data = cli.post("/api/render_realistic", json=body).json()
    assert data["images"]["living"].startswith("data:image/png;base64,")
