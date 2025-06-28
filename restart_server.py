from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "loradb" / "templates"

app = FastAPI(title="Restarting")

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

@app.get("/", response_class=HTMLResponse)
async def restart_page():
    template = env.get_template("restart.html")
    return template.render(title="Restarting")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
