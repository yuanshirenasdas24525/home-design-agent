# tests/test_scheme_generator.py
from hda.models import FloorPlan, Room, Requirement, Scheme
from hda.scheme_generator import generate_scheme, check_constraints
from hda.providers.fake import FakeProvider


def _fp():
    return FloorPlan(
        community="阳光花园", layout_type="三室两厅", total_area=89.0,
        rooms=[Room(room_id="living_room", name="客厅", area=22.5,
                    polygon=[(0, 0), (5, 0), (5, 4.5), (0, 4.5)])],
    )


def test_generate_scheme_covers_every_room():
    fp = _fp()
    scheme = generate_scheme(FakeProvider(), fp, Requirement(style="北欧"))
    assert {r.room_id for r in scheme.rooms} == {"living_room"}
    assert scheme.floorplan_ref  # 关联户型


def test_check_constraints_marks_load_bearing_pass_when_no_wall_change():
    fp = _fp()
    scheme = generate_scheme(FakeProvider(), fp, Requirement(constraints=["不拆承重墙"]))
    checks = check_constraints(scheme, Requirement(constraints=["不拆承重墙"]))
    assert any(c.rule == "不拆承重墙" and c.status == "pass" for c in checks)


def test_check_constraints_fails_missing_required_room():
    fp = _fp()
    scheme = generate_scheme(FakeProvider(), fp, Requirement())
    # 要求"要书房"，但户型/方案里没有书房 -> fail
    checks = check_constraints(scheme, Requirement(preferences=["要书房"]))
    assert any(c.rule == "要书房" and c.status == "fail" for c in checks)
