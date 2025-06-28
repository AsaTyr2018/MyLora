from fastapi import FastAPI
from loradb.plugins.manager import hookimpl

@hookimpl
def setup(app: FastAPI) -> None:
    @app.get('/hello')
    async def hello():
        return {'message': 'Hello from plugin!'}
