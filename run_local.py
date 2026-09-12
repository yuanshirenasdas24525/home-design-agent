import os
import uvicorn
from hda.web.app import create_app
from hda.providers.fake import FakeProvider
from hda.providers.factory import load_env, build_provider_from_env, build_wanx_from_env

if __name__ == "__main__":
    load_env()
    # 有真实 Key 就用真实 Provider（智谱看图/DeepSeek文本/智谱出图），否则回退 Fake
    if os.environ.get("DEEPSEEK_API_KEY") and os.environ.get("ZHIPU_API_KEY"):
        provider = build_provider_from_env()
        print("使用真实 Provider：智谱 GLM-4V / DeepSeek / 智谱 CogView")
    else:
        provider = FakeProvider()
        print("未检测到 API Key，使用 FakeProvider（假数据）")
    wanx = build_wanx_from_env()
    print("通义万相实景图：", "已启用" if wanx else "未配置(缺 DASHSCOPE_API_KEY)")
    uvicorn.run(create_app(provider, wanx=wanx), host="127.0.0.1", port=8000)
