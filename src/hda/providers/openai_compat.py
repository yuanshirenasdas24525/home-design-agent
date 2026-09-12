# src/hda/providers/openai_compat.py
from __future__ import annotations
import base64
import json
from typing import Callable
from openai import OpenAI
from hda.models import FloorPlan, Requirement, Scheme

ImageCall = Callable[[str, str], bytes]  # (prompt, reference_svg) -> image bytes


class OpenAICompatProvider:
    """面向 OpenAI 兼容协议的真实 Provider。base_url/model 可切换不同厂商。

    图像生成各家协议不同，通过 image_call 回调注入，避免写死某一家。
    """

    def __init__(self, api_key: str, base_url: str, model: str,
                 image_call: ImageCall | None = None):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._image_call = image_call

    @staticmethod
    def _extract_json(text: str) -> dict:
        """容错解析：部分模型会用 ```json ... ``` 包裹或加前后缀文字。"""
        s = text.strip()
        if s.startswith("```"):
            s = s.split("```", 2)[1]
            if s.startswith("json"):
                s = s[4:]
            s = s.strip()
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            start, end = s.find("{"), s.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(s[start:end + 1])
            raise

    def _chat_json(self, system: str, user_text: str, image_bytes: bytes | None = None,
                   force_json: bool = True) -> dict:
        content: list[dict] = [{"type": "text", "text": user_text}]
        if image_bytes is not None:
            b64 = base64.b64encode(image_bytes).decode()
            content.append({"type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64}"}})
        kwargs: dict = {
            "model": self._model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": content}],
            "temperature": 0.3,
        }
        if force_json:
            kwargs["response_format"] = {"type": "json_object"}
        resp = self._client.chat.completions.create(**kwargs)
        return self._extract_json(resp.choices[0].message.content)

    def recognize_floorplan(self, image_bytes: bytes, hint: dict) -> FloorPlan:
        system = ("你是户型图识别专家。只输出一个 JSON 对象，不要任何解释、不要代码块包裹。"
                  "字段：community,layout_type,total_area,"
                  "rooms[{room_id,name,area,polygon}],doors[{room_a,room_b,pos}],"
                  "windows[{room_id,pos}]。room_id 用英文小写下划线（如 living_room）。"
                  "polygon/pos 为 [x,y] 数组，坐标单位米。优先保证房间拓扑正确。")
        # 视觉模型（如 GLM-4V）未必支持 response_format，故不强制 JSON 模式，靠容错解析。
        data = self._chat_json(system, f"小区提示：{hint.get('community','')}",
                               image_bytes, force_json=False)
        return FloorPlan.model_validate(data)

    def parse_requirement(self, options: dict, transcript: str) -> Requirement:
        system = ("你把装修需求解析为 JSON：style,budget_level(低/中/高),household,"
                  "constraints[],preferences[]。选项框字段为权威，口述仅补充；"
                  "冲突以选项框为准。硬约束务必抽全放入 constraints。")
        user = f"选项框：{json.dumps(options, ensure_ascii=False)}\n口述：{transcript}"
        data = self._chat_json(system, user)
        for k, v in options.items():  # 选项框为准
            if v:
                data[k] = v
        return Requirement.model_validate(data)

    def generate_scheme(self, floorplan: FloorPlan, requirement: Requirement) -> Scheme:
        system = ("你是资深室内设计师。只输出一个 JSON 对象，不要解释、不要代码块。Scheme 字段："
                  "scheme_id,floorplan_ref,style,palette[],budget_level,"
                  "rooms[{room_id,name,furniture[{item,pos,facing,size}],finishes{},"
                  "soft[],render_prompt}]。pos 为 [x,y]（米，房间内坐标）；"
                  "size 为 [长,宽] 或 [长,宽,高]（米）。room_id 必须与输入户型的 room_id 一致。"
                  "每个房间都要写 render_prompt（含风格/家具/材质/视角）。"
                  "家具 pos 必须落在对应房间 polygon 内，不得挡门。")
        user = (f"户型：{floorplan.model_dump_json()}\n"
                f"需求：{requirement.model_dump_json()}")
        data = self._chat_json(system, user)
        return Scheme.model_validate(data)

    def render_perspective(self, prompt: str, reference_svg: str) -> bytes:
        if self._image_call is None:
            raise RuntimeError("该 Provider 未配置 image_call，无法生成实景图")
        return self._image_call(prompt, reference_svg)
