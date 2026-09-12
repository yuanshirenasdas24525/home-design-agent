# tests/test_requirement_parser.py
from hda.requirement_parser import parse_requirement
from hda.providers.fake import FakeProvider


def test_options_win_over_transcript_for_style():
    # 选项框给了风格，口述里的风格不应覆盖
    req = parse_requirement(FakeProvider(), options={"style": "北欧"},
                            transcript="我其实想要美式")
    assert req.style == "北欧"


def test_hard_constraints_extracted_from_transcript():
    req = parse_requirement(FakeProvider(), options={"style": "北欧"},
                            transcript="不拆承重墙")
    assert "不拆承重墙" in req.constraints
