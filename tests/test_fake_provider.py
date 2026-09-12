from hda.models import FloorPlan, Requirement, Scheme
from hda.providers.fake import FakeProvider


def test_fake_vision_returns_floorplan():
    p = FakeProvider()
    fp = p.recognize_floorplan(image_bytes=b"fake-image", hint={"community": "阳光花园"})
    assert isinstance(fp, FloorPlan)
    assert fp.community == "阳光花园"
    assert len(fp.rooms) >= 1


def test_fake_llm_parses_requirement():
    p = FakeProvider()
    req = p.parse_requirement(options={"style": "北欧"}, transcript="想要个书房，不拆承重墙")
    assert isinstance(req, Requirement)
    assert req.style == "北欧"
    assert "不拆承重墙" in req.constraints


def test_fake_llm_generates_scheme():
    p = FakeProvider()
    fp = p.recognize_floorplan(b"x", {})
    req = Requirement(style="北欧")
    scheme = p.generate_scheme(fp, req)
    assert isinstance(scheme, Scheme)
    assert len(scheme.rooms) == len(fp.rooms)


def test_fake_image_returns_bytes():
    p = FakeProvider()
    img = p.render_perspective(prompt="北欧客厅", reference_svg="<svg/>")
    assert isinstance(img, bytes) and len(img) > 0
