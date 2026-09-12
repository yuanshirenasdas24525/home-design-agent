# src/hda/providers/zhipu_image.py
from __future__ import annotations
import urllib.request
from openai import OpenAI


class ZhipuImageProvider:
    """智谱 CogView 文生图，实现 ImageProvider.render_perspective。

    智谱的 images/generations 与 OpenAI 协议兼容，返回图片 URL；这里生成后
    把 URL 下载成字节返回，供上层转 data URL 展示。
    reference_svg 暂不用于约束（CogView 不吃构图参考图），仅靠 prompt 控制；
    后续换自建 SD+ControlNet 时在此接入参考图。
    """

    def __init__(self, api_key: str, base_url: str, model: str = "cogview-3-flash",
                 size: str = "1024x1024"):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._size = size

    def render_perspective(self, prompt: str, reference_svg: str) -> bytes:
        resp = self._client.images.generate(
            model=self._model, prompt=prompt, size=self._size)
        url = resp.data[0].url
        with urllib.request.urlopen(url, timeout=60) as r:
            return r.read()
