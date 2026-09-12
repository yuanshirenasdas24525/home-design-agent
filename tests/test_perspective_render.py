# tests/test_perspective_render.py
from hda.models import Scheme, RoomScheme
from hda.perspective_render import render_perspectives
from hda.providers.fake import FakeProvider


def test_render_one_image_per_room():
    scheme = Scheme(scheme_id="s", floorplan_ref="f", rooms=[
        RoomScheme(room_id="living_room", name="客厅", render_prompt="北欧客厅"),
        RoomScheme(room_id="master_bedroom", name="主卧", render_prompt="北欧主卧"),
    ])
    images = render_perspectives(FakeProvider(), scheme, reference_svg="<svg/>")
    assert set(images.keys()) == {"living_room", "master_bedroom"}
    assert all(isinstance(v, bytes) and len(v) > 0 for v in images.values())


def test_render_skips_rooms_without_prompt():
    scheme = Scheme(scheme_id="s", floorplan_ref="f", rooms=[
        RoomScheme(room_id="balcony", name="阳台", render_prompt=""),
    ])
    images = render_perspectives(FakeProvider(), scheme, reference_svg="<svg/>")
    assert images == {}
