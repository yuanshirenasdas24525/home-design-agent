from hda.models import FloorPlan, Room, Requirement, Scheme
from hda.providers.composite import CompositeProvider


class _Vision:
    def recognize_floorplan(self, image_bytes, hint):
        return FloorPlan(community=hint.get("community", ""), rooms=[
            Room(room_id="r1", name="客厅", area=20, polygon=[(0, 0), (4, 0), (4, 5), (0, 5)])])


class _LLM:
    def parse_requirement(self, options, transcript):
        return Requirement(style=options.get("style", ""))

    def generate_scheme(self, floorplan, requirement):
        return Scheme(scheme_id="s", floorplan_ref="f", style=requirement.style)


class _Image:
    def render_perspective(self, prompt, reference_svg):
        return b"IMG:" + prompt.encode()


def _composite():
    return CompositeProvider(vision=_Vision(), llm=_LLM(), image=_Image())


def test_routes_vision_to_vision_provider():
    fp = _composite().recognize_floorplan(b"x", {"community": "阳光花园"})
    assert fp.community == "阳光花园"
    assert fp.rooms[0].name == "客厅"


def test_routes_text_to_llm_provider():
    c = _composite()
    req = c.parse_requirement({"style": "北欧"}, "随便")
    assert req.style == "北欧"
    scheme = c.generate_scheme(FloorPlan(rooms=[]), req)
    assert scheme.style == "北欧"


def test_routes_image_to_image_provider():
    img = _composite().render_perspective("北欧客厅", "<svg/>")
    assert img.startswith(b"IMG:")
    assert "北欧客厅".encode() in img
