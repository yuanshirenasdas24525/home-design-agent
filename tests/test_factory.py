import os
import pytest
from hda.providers.composite import CompositeProvider
from hda.providers.factory import build_provider_from_env, load_env


def test_load_env_does_not_override_existing(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("FOO_KEY=fromfile\n# comment\nBAR_KEY=\"quoted\"\n", encoding="utf-8")
    monkeypatch.setenv("FOO_KEY", "preset")
    load_env(env)
    assert os.environ["FOO_KEY"] == "preset"   # 已存在不覆盖
    assert os.environ["BAR_KEY"] == "quoted"    # 去掉引号


def test_build_raises_without_keys(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    # 防止读到项目根下真实 .env
    monkeypatch.chdir("/tmp")
    with pytest.raises(RuntimeError, match="缺少 API Key"):
        build_provider_from_env()


def test_build_assembles_composite_with_keys(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setenv("ZHIPU_API_KEY", "zp.test")
    monkeypatch.chdir("/tmp")  # 不读真实 .env
    provider = build_provider_from_env()
    assert isinstance(provider, CompositeProvider)
