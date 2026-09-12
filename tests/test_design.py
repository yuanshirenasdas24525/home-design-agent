from fastapi.testclient import TestClient
from hda.web.app import create_app
from hda.providers.fake import FakeProvider


def _client():
    return TestClient(create_app(provider=FakeProvider()))


def test_design_returns_furnished_plan_and_scheme():
    fp = {
        "community": "", "layout_type": "", "total_area": 0, "doors": [], "windows": [],
        "rooms": [{"room_id": "living", "name": "客厅", "area": 22,
                   "polygon": [[0, 0], [5, 0], [5, 4.5], [0, 4.5]]}],
    }
    body = {"floorplan": fp, "options": {"style": "北欧"}, "transcript": "不拆承重墙"}
    resp = _client().post("/api/design", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["colored_plan_svg"].startswith("<svg")
    assert len(data["scheme"]["rooms"]) == 1
    assert data["scheme"]["rooms"][0]["furniture"]  # 有家具
