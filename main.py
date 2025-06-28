from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

import config
from loradb.api import router as api_router, indexer, plugin_manager

app = FastAPI(title="LoRA Database")

app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")

UPLOAD_DIR = Path(config.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
env = Environment(loader=FileSystemLoader(config.TEMPLATE_DIR))

app.include_router(api_router)
plugin_manager.load_enabled(app)

@app.get("/", response_class=HTMLResponse)
async def index():
    template = env.get_template("index.html")
    stats = {
        "lora_count": indexer.lora_count(),
        "preview_count": indexer.preview_count(),
        "category_count": indexer.category_count(),
        "top_categories": indexer.top_categories(limit=20),
    }
    return template.render(title="LoRA Database", stats=stats)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
