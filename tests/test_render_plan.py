from fastapi.testclient import TestClient
from hda.web.app import create_app
from hda.providers.fake import FakeProvider


def _client():
    return TestClient(create_app(provider=FakeProvider()))


def test_render_plan_from_traced_geometry():
    fp = {
        "community": "", "layout_type": "", "total_area": 0,
        "doors": [], "windows": [],
        "rooms": [
            {"room_id": "r1", "name": "客餐厅", "area": 31.0,
             "polygon": [[0, 0], [4, 0], [4, 7], [0, 7]]},
            {"room_id": "r2", "name": "主卧", "area": 13.6,
             "polygon": [[4, 4], [8, 4], [8, 7], [4, 7]]},
        ],
    }
    resp = _client().post("/api/render_plan", json={"floorplan": fp})
    assert resp.status_code == 200
    svg = resp.json()["colored_plan_svg"]
    assert svg.startswith("<svg")
    assert "客餐厅" in svg and "主卧" in svg


def test_trace_page_served():
    resp = _client().get("/trace")
    assert resp.status_code == 200
    assert "描线" in resp.text
