from loradb.plugins.manager import hookimpl
from loradb.api import frontend

@hookimpl
def setup(app):
    original_render_grid = frontend.render_grid

    def render_grid_with_extream(*args, **kwargs):
        html = original_render_grid(*args, **kwargs)
        return html.replace('LoRA Gallery', 'LoRA Gallery - Extream!')

    frontend.render_grid = render_grid_with_extream
