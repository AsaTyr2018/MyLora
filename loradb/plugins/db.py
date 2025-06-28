import sqlite3
from pathlib import Path
from typing import Dict


class PluginStateDB:
    """Persist plugin enabled state using SQLite."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS plugin_state (id TEXT PRIMARY KEY, enabled INTEGER)"
        )
        self.conn.commit()

    def get_all(self) -> Dict[str, bool]:
        cur = self.conn.cursor()
        rows = cur.execute("SELECT id, enabled FROM plugin_state").fetchall()
        return {r[0]: bool(r[1]) for r in rows}

    def set_state(self, plugin_id: str, enabled: bool) -> None:
        self.conn.execute(
            "INSERT INTO plugin_state (id, enabled) VALUES (?, ?) "
            "ON CONFLICT(id) DO UPDATE SET enabled=excluded.enabled",
            (plugin_id, int(enabled)),
        )
        self.conn.commit()
