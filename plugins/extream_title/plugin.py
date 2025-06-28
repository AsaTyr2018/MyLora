from loradb.plugins.manager import hookimpl
from loradb.api import frontend

original_render_grid = None

@hookimpl
def setup(app):
    global original_render_grid
    original_render_grid = frontend.render_grid

    def render_grid_with_extream(*args, **kwargs):
        html = original_render_grid(*args, **kwargs)
        return html.replace('LoRA Gallery', 'LoRA Gallery - Extream!')

    frontend.render_grid = render_grid_with_extream


@hookimpl
def teardown(app):
    global original_render_grid
    if original_render_grid:
        frontend.render_grid = original_render_grid
        original_render_grid = None
