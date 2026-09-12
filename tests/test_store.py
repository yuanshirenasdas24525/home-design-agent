from hda.models import FloorPlan, Room, Scheme, RoomScheme
from hda.store import CaseStore


def _fp():
    return FloorPlan(rooms=[Room(room_id="r1", name="客厅", area=20,
                                 polygon=[(0, 0), (4, 0), (4, 5), (0, 5)])])


def _scheme():
    return Scheme(scheme_id="s", floorplan_ref="f",
                  rooms=[RoomScheme(room_id="r1", name="客厅")])


def test_save_and_get(tmp_path):
    st = CaseStore(tmp_path / "c.db")
    cid = st.save("阳光花园", "三室两厅", "北欧", _fp(), _scheme(), "<svg/>")
    got = st.get(cid)
    assert got["community"] == "阳光花园"
    assert got["floorplan"]["rooms"][0]["name"] == "客厅"
    assert got["svg"] == "<svg/>"


def test_list_filters_by_community(tmp_path):
    st = CaseStore(tmp_path / "c.db")
    st.save("阳光花园", "三室两厅", "北欧", _fp(), _scheme(), "")
    st.save("翠湖苑", "两室一厅", "中式", _fp(), _scheme(), "")
    only = st.list(community="阳光花园")
    assert len(only) == 1 and only[0]["community"] == "阳光花园"
    assert len(st.list()) == 2
