import uvicorn
from hda.web.app import create_app
from hda.providers.fake import FakeProvider

if __name__ == "__main__":
    uvicorn.run(create_app(FakeProvider()), host="127.0.0.1", port=8000)
