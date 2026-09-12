# src/hda/providers/wanx_image.py
from __future__ import annotations
import base64
import json
import time
import urllib.request

_BASE = "https://dashscope.aliyuncs.com/api/v1"
_CREATE = _BASE + "/services/aigc/image2image/image-synthesis"
_TASK = _BASE + "/tasks/"


class WanxImageProvider:
    """通义万相图像编辑：doodle（线稿生图）——喂结构线稿 PNG，出跟结构对上的实景。

    异步任务：创建 → 轮询 → 取 output.results[].url → 下载字节。
    """

    def __init__(self, api_key: str, model: str = "wanx2.1-imageedit",
                 poll_interval: float = 5.0, timeout: float = 180.0):
        self._key = api_key
        self._model = model
        self._interval = poll_interval
        self._timeout = timeout

    def _headers(self, async_task: bool = False) -> dict:
        h = {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"}
        if async_task:
            h["X-DashScope-Async"] = "enable"
        return h

    def doodle(self, sketch_png: bytes, prompt: str) -> bytes:
        """线稿 PNG + 提示词 → 实景图字节（跟线稿结构一致）。"""
        data_uri = "data:image/png;base64," + base64.b64encode(sketch_png).decode()
        body = json.dumps({
            "model": self._model,
            "input": {"function": "doodle", "prompt": prompt, "base_image_url": data_uri},
            "parameters": {"n": 1},
        }).encode()
        req = urllib.request.Request(_CREATE, data=body, method="POST",
                                     headers=self._headers(async_task=True))
        task_id = json.load(urllib.request.urlopen(req, timeout=60))["output"]["task_id"]

        deadline = time.time() + self._timeout
        while time.time() < deadline:
            time.sleep(self._interval)
            g = urllib.request.Request(_TASK + task_id, headers=self._headers())
            out = json.load(urllib.request.urlopen(g, timeout=30))["output"]
            st = out["task_status"]
            if st == "SUCCEEDED":
                url = out["results"][0]["url"]
                return urllib.request.urlopen(url, timeout=60).read()
            if st == "FAILED":
                raise RuntimeError(f"通义万相任务失败: {out.get('message', out)}")
        raise TimeoutError("通义万相任务超时")
