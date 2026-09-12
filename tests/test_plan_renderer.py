# tests/test_plan_renderer.py
from hda.models import FloorPlan, Room, Scheme, RoomScheme, FurnitureItem
from hda.plan_renderer import render_colored_plan


def _fp():
    return FloorPlan(rooms=[
        Room(room_id="living_room", name="客厅", area=22.5,
             polygon=[(0, 0), (5, 0), (5, 4.5), (0, 4.5)]),
    ])


def _scheme():
    return Scheme(scheme_id="s", floorplan_ref="f", rooms=[
        RoomScheme(room_id="living_room", name="客厅",
                   furniture=[FurnitureItem(item="沙发", pos=(1, 1), size=(2, 1))]),
    ])


def test_render_produces_svg_with_room_and_furniture():
    svg = render_colored_plan(_fp(), _scheme())
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    assert "客厅" in svg      # 房间名标注
    assert "沙发" in svg      # 家具标注


def test_render_scales_to_viewbox():
    svg = render_colored_plan(_fp(), _scheme())
    assert "viewBox" in svg
