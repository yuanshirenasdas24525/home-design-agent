from fastapi.testclient import TestClient
from hda.web.app import create_app
from hda.providers.fake import FakeProvider
from hda.store import CaseStore


def _client(tmp_path):
    return TestClient(create_app(provider=FakeProvider(), store=CaseStore(tmp_path / "c.db")))


def _payload():
    fp = {"community": "", "layout_type": "", "total_area": 0, "doors": [], "windows": [],
          "rooms": [{"room_id": "r1", "name": "客厅", "area": 20,
                     "polygon": [[0, 0], [4, 0], [4, 5], [0, 5]]}]}
    scheme = {"scheme_id": "s", "floorplan_ref": "f",
              "rooms": [{"room_id": "r1", "name": "客厅"}]}
    return {"community": "阳光花园", "layout_type": "三室两厅", "style": "北欧",
            "floorplan": fp, "scheme": scheme, "svg": "<svg/>"}


def test_save_then_list_then_get(tmp_path):
    cli = _client(tmp_path)
    cid = cli.post("/api/save_case", json=_payload()).json()["id"]

    lst = cli.get("/api/cases", params={"community": "阳光花园"}).json()["cases"]
    assert any(c["id"] == cid for c in lst)

    got = cli.get(f"/api/cases/{cid}").json()
    assert got["style"] == "北欧" and got["svg"] == "<svg/>"


def test_cases_page_served(tmp_path):
    resp = _client(tmp_path).get("/cases")
    assert resp.status_code == 200
    assert "案例库" in resp.text
