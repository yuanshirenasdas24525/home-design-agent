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
