from hda.providers.openai_compat import OpenAICompatProvider

_extract = OpenAICompatProvider._extract_json


def test_plain_json():
    assert _extract('{"a": 1}') == {"a": 1}


def test_code_fenced_json():
    assert _extract('```json\n{"a": 1}\n```') == {"a": 1}


def test_json_with_surrounding_text():
    assert _extract('好的，结果如下：\n{"a": 1}\n以上。') == {"a": 1}
