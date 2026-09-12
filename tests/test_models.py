from hda.models import FloorPlan, Room, Requirement, Scheme, RoomScheme, FurnitureItem, ConstraintCheck


def test_floorplan_roundtrips():
    fp = FloorPlan(
        community="阳光花园", layout_type="三室两厅", total_area=89.0,
        rooms=[Room(room_id="living_room", name="客厅", area=22.5,
                    polygon=[(0, 0), (5, 0), (5, 4.5), (0, 4.5)])],
        doors=[], windows=[],
    )
    assert fp.rooms[0].room_id == "living_room"
    assert FloorPlan.model_validate(fp.model_dump()) == fp


def test_scheme_room_is_independent_unit():
    scheme = Scheme(
        scheme_id="s1", floorplan_ref="fp1",
        style="北欧", palette=["米白", "浅木"], budget_level="中",
        rooms=[RoomScheme(
            room_id="living_room", name="客厅",
            furniture=[FurnitureItem(item="布艺三人沙发", pos=(1.0, 1.0), facing="北", size=(2.4, 0.9))],
            finishes={"地面": "浅色木地板"}, soft=["落地灯"],
            render_prompt="北欧风客厅, 布艺沙发...",
        )],
        constraints_check=[ConstraintCheck(rule="不拆承重墙", status="pass")],
    )
    assert scheme.rooms[0].furniture[0].item == "布艺三人沙发"
    assert scheme.get_room("living_room").name == "客厅"
