# MyLora Plugin System

MyLora can be extended using a lightweight plugin system powered by the
[Pluggy](https://pluggy.readthedocs.io/) framework. Plugins live in the
`plugins` directory and can be toggled on or off from the **Plugin
Administration** page of the web UI (`/plugins`).

## How it works

On startup the application scans the `plugins` directory for sub
folders. Each folder that contains a `manifest.json` file and a
`plugin.py` module is considered a plugin. The manifest provides basic
metadata while `plugin.py` contains the actual implementation.

Enabled plugins are imported dynamically and may register new FastAPI
routes or run arbitrary startup code. When a plugin is disabled the
routes added during its setup are removed again. The enabled/disabled
state is stored in `loradb/plugin_state.db` so that the configuration is
persisted across restarts.

### Hook specifications

Plugins communicate with MyLora through two hooks:

- `setup(app: FastAPI)` – called once when the plugin is loaded. The
  passed `app` instance can be used to add routes or any other FastAPI
  configuration.
- `teardown(app: FastAPI)` – called when a plugin is unloaded. Use this
  to clean up resources or background tasks.

Both hooks are defined in `loradb.plugins.manager` and exposed via the
`hookimpl` decorator.

## Writing your own plugin

1. Create a new folder inside `plugins` (e.g. `my_plugin`).
2. Add a `manifest.json` with at least the following fields:

   ```json
   {
     "name": "My Plugin",
     "description": "What it does",
     "version": "0.1"
   }
   ```

3. Inside the same folder add a `plugin.py` file. Import the
   `hookimpl` decorator and implement the hooks you need:

   ```python
   from fastapi import FastAPI
   from loradb.plugins.manager import hookimpl

   @hookimpl
   def setup(app: FastAPI) -> None:
       @app.get('/hello')
       async def hello():
           return {'message': 'Hello from my plugin!'}
   ```

   The above example registers a new `/hello` route when the plugin is
   enabled.

4. Start the server and open `/plugins` to enable or disable your
   plugin. After toggling a plugin you may need to press **Refresh
   Server** to restart the application so the change takes effect.

### Requirements

Plugins run inside the same Python environment as MyLora. If your plugin
needs additional third party packages they must be installed in that
environment as well. Make sure to list them in a separate requirements
file or document them in your plugin's README so they can be installed
before enabling the plugin.

## Example

A minimal working example can be found in `plugins/sample_plugin`. It
adds a simple `/hello` endpoint and demonstrates the expected directory
layout.

