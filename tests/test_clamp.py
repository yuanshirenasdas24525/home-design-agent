from hda.models import FloorPlan, Room, Scheme, RoomScheme, FurnitureItem
from hda.scheme_generator import clamp_furniture_to_rooms


def test_clamp_pulls_furniture_inside_room():
    fp = FloorPlan(rooms=[Room(room_id="living", name="客厅", area=20,
                               polygon=[(0, 0), (4, 0), (4, 5), (0, 5)])])
    scheme = Scheme(scheme_id="s", floorplan_ref="f", rooms=[
        RoomScheme(room_id="living", name="客厅", furniture=[
            FurnitureItem(item="沙发", pos=(99, 99), size=[2, 1]),  # 明显在房间外
        ])])
    clamp_furniture_to_rooms(scheme, fp)
    x, y = scheme.rooms[0].furniture[0].pos
    # 家具矩形应完全落在房间内
    assert 0 <= x - 1 and x + 1 <= 4
    assert 0 <= y - 0.5 and y + 0.5 <= 5


def test_clamp_matches_room_by_name_when_id_differs():
    fp = FloorPlan(rooms=[Room(room_id="r1", name="主卧", area=12,
                               polygon=[(0, 0), (3, 0), (3, 4), (0, 4)])])
    scheme = Scheme(scheme_id="s", floorplan_ref="f", rooms=[
        RoomScheme(room_id="master", name="主卧", furniture=[
            FurnitureItem(item="床", pos=(10, 10), size=[1.5, 2])])])
    clamp_furniture_to_rooms(scheme, fp)
    x, y = scheme.rooms[0].furniture[0].pos
    assert x <= 3 and y <= 4
