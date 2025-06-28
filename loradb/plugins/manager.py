import json
import importlib.util
from pathlib import Path
from typing import Dict, List, Any

import pluggy
from fastapi import FastAPI

pm_namespace = "mylora"

hookspec = pluggy.HookspecMarker(pm_namespace)
hookimpl = pluggy.HookimplMarker(pm_namespace)


class HookSpecs:
    @hookspec
    def setup(self, app: FastAPI) -> None:
        """Called when the plugin is loaded."""


class PluginManager:
    def __init__(self, plugins_dir: Path) -> None:
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(exist_ok=True)
        self.status_path = self.plugins_dir / "plugins_status.json"
        if self.status_path.exists():
            self.status: Dict[str, bool] = json.loads(self.status_path.read_text())
        else:
            self.status = {}
        self.manager = pluggy.PluginManager(pm_namespace)
        self.manager.add_hookspecs(HookSpecs)
        self.loaded: Dict[str, object] = {}
        self.loaded_routes: Dict[str, List[Any]] = {}

    def _save_status(self) -> None:
        self.status_path.write_text(json.dumps(self.status, indent=2))

    def discover(self) -> List[Dict[str, str]]:
        """Return list of discovered plugins with metadata and enabled flag."""
        plugins: List[Dict[str, str]] = []
        for pdir in sorted(self.plugins_dir.iterdir()):
            if not pdir.is_dir():
                continue
            manifest = pdir / "manifest.json"
            if not manifest.exists():
                continue
            try:
                meta = json.loads(manifest.read_text())
            except Exception:
                continue
            meta.setdefault("name", pdir.name)
            meta["id"] = pdir.name
            meta["enabled"] = self.status.get(pdir.name, False)
            plugins.append(meta)
        return plugins

    def load_enabled(self, app: FastAPI) -> None:
        for info in self.discover():
            if info["enabled"]:
                self._load_plugin(info["id"], app)

    def _load_plugin(self, plugin_id: str, app: FastAPI) -> None:
        if plugin_id in self.loaded:
            return
        plugin_dir = self.plugins_dir / plugin_id
        plugin_py = plugin_dir / "plugin.py"
        if not plugin_py.exists():
            return
        spec = importlib.util.spec_from_file_location(f"plugins.{plugin_id}", plugin_py)
        if not spec or not spec.loader:
            return
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.manager.register(mod, plugin_id)
        self.loaded[plugin_id] = mod
        existing = list(app.router.routes)
        self.manager.hook.setup(app=app)
        new_routes = [r for r in app.router.routes if r not in existing]
        self.loaded_routes[plugin_id] = new_routes

    def _unload_plugin(self, plugin_id: str, app: FastAPI | None) -> None:
        if plugin_id not in self.loaded:
            return
        if app is not None:
            for route in self.loaded_routes.get(plugin_id, []):
                if route in app.router.routes:
                    app.router.routes.remove(route)
        self.manager.unregister(name=plugin_id)
        self.loaded.pop(plugin_id, None)
        self.loaded_routes.pop(plugin_id, None)

    def enable(self, plugin_id: str, app: FastAPI) -> None:
        self.status[plugin_id] = True
        self._save_status()
        self._load_plugin(plugin_id, app)

    def disable(self, plugin_id: str, app: FastAPI | None = None) -> None:
        self.status[plugin_id] = False
        self._save_status()
        self._unload_plugin(plugin_id, app)

