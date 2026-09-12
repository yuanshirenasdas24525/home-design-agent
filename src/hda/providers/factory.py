# src/hda/providers/factory.py
from __future__ import annotations
import os
from pathlib import Path
from hda.providers.openai_compat import OpenAICompatProvider
from hda.providers.zhipu_image import ZhipuImageProvider
from hda.providers.composite import CompositeProvider

# 各家默认端点 / 模型（均可用环境变量覆盖）
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"


def load_env(path: str | os.PathLike = ".env") -> None:
    """最简 .env 读取：KEY=VALUE 每行一条，# 开头为注释。已存在的环境变量不覆盖。"""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def build_provider_from_env() -> CompositeProvider:
    """按 spec 的分工装配真实 Provider：智谱看图 / DeepSeek 文本 / 智谱出图。"""
    load_env()
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    zhipu_key = os.environ.get("ZHIPU_API_KEY")
    if not deepseek_key or not zhipu_key:
        raise RuntimeError(
            "缺少 API Key：请在 .env 中设置 DEEPSEEK_API_KEY 和 ZHIPU_API_KEY")

    vision = OpenAICompatProvider(
        api_key=zhipu_key,
        base_url=os.environ.get("ZHIPU_BASE_URL", ZHIPU_BASE_URL),
        model=os.environ.get("VISION_MODEL", "glm-4v-flash"),
    )
    llm = OpenAICompatProvider(
        api_key=deepseek_key,
        base_url=os.environ.get("DEEPSEEK_BASE_URL", DEEPSEEK_BASE_URL),
        model=os.environ.get("LLM_MODEL", "deepseek-chat"),
    )
    image = ZhipuImageProvider(
        api_key=zhipu_key,
        base_url=os.environ.get("ZHIPU_BASE_URL", ZHIPU_BASE_URL),
        model=os.environ.get("IMAGE_MODEL", "cogview-3-flash"),
    )
    return CompositeProvider(vision=vision, llm=llm, image=image)
