from hda.models import GridPlan, GridRoom
from hda.grid import build_grid_lines, snap_rooms


def test_build_grid_lines_unions_top_and_bottom():
    gp = GridPlan(top_dims=[4150, 2900, 3000], bottom_dims=[4150, 1700, 4200],
                  left_dims=[1500, 7100, 3000], right_dims=[1500, 5050, 3850, 1200])
    x, y = build_grid_lines(gp)
    assert x == [0.0, 4.15, 5.85, 7.05, 10.05]
    assert y == [0.0, 1.5, 6.55, 8.6, 10.4, 11.6]


def test_snap_rooms_produces_grid_aligned_rectangles():
    gp = GridPlan(top_dims=[4], bottom_dims=[4], left_dims=[3, 4], right_dims=[3, 4],
                  rooms=[
                      GridRoom(name="A", area=12, bbox=[0.0, 0.0, 1.0, 0.5]),
                      GridRoom(name="B", area=16, bbox=[0.0, 0.5, 1.0, 1.0]),
                  ])
    x, y = build_grid_lines(gp)          # x=[0,4]  y=[0,3,7]
    fp = snap_rooms(gp, x, y)
    assert len(fp.rooms) == 2
    a = fp.rooms[0]
    # 每个房间顶点都落在网格线上
    for px, py in a.polygon:
        assert px in x and py in y


def test_snap_rooms_empty_when_no_rooms():
    gp = GridPlan(top_dims=[4], left_dims=[3])
    x, y = build_grid_lines(gp)
    assert snap_rooms(gp, x, y).rooms == []
