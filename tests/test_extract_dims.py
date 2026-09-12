from fastapi.testclient import TestClient
from hda.web.app import create_app
from hda.providers.fake import FakeProvider


def _client():
    return TestClient(create_app(provider=FakeProvider()))


def test_extract_dims_returns_grid_and_floorplan():
    files = {"image": ("plan.png", b"fakeimg", "image/png")}
    resp = _client().post("/api/extract_dims", files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert body["dims"]["top_dims"] == [4150, 2900, 3000]
    assert body["x_lines"][0] == 0.0 and body["x_lines"][-1] == 10.05
    assert len(body["floorplan"]["rooms"]) >= 1


def test_grid_page_served():
    resp = _client().get("/grid")
    assert resp.status_code == 200
    assert "半自动" in resp.text
