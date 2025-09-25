"""MyLora export utility.

Download LoRA models along with their preview images from a running MyLora
instance and organise them into a structured folder layout for offline use.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import httpx

# --- Configuration ---------------------------------------------------------
# Provide the URL of your MyLora host and the credentials used to sign in.
# Example: "http://127.0.0.1:5000"
MYLORA_HOST = "http://127.0.0.1:5000"
MYLORA_USERNAME = ""
MYLORA_PASSWORD = ""


@dataclass
class LoraEntry:
    """Minimal metadata needed for an export task."""

    filename: str
    name: str
    tags: str
    categories: list[str]

    @property
    def stem(self) -> str:
        return Path(self.filename).stem


class PreviewImageParser(HTMLParser):
    """Parse preview image URLs from a MyLora detail page."""

    def __init__(self) -> None:
        super().__init__()
        self._urls: set[str] = set()

    def handle_starttag(self, tag: str, attrs: Iterable[tuple[str, str | None]]) -> None:
        if tag != "img":
            return
        for key, value in attrs:
            if key == "src" and value and value.startswith("/uploads/"):
                self._urls.add(value)

    @property
    def urls(self) -> list[str]:
        return sorted(self._urls)


class MyLoraExporter:
    """Export LoRA models and preview images from a MyLora instance."""

    def __init__(self, base_url: str, username: str, password: str) -> None:
        if not base_url:
            raise ValueError("MYLORA_HOST is not configured")
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.client = httpx.Client(base_url=self.base_url, follow_redirects=False)

    def login(self) -> None:
        """Authenticate against the MyLora instance if credentials are provided."""

        if not self.username or not self.password:
            return
        resp = self.client.post(
            "/login",
            data={"username": self.username, "password": self.password},
            headers={"Accept": "text/html"},
        )
        if resp.status_code != 303:
            raise RuntimeError(
                "Login failed – verify MYLORA_USERNAME and MYLORA_PASSWORD"
            )

    def fetch_entries(self, limit: int = 100) -> list[LoraEntry]:
        """Return all LoRA entries available in MyLora."""

        entries: dict[str, LoraEntry] = {}
        offset = 0
        while True:
            resp = self.client.get(
                "/grid_data",
                params={"q": "*", "limit": limit, "offset": offset},
                headers={"Accept": "application/json"},
            )
            if resp.status_code == 303:
                raise RuntimeError("Access denied. Please provide valid credentials.")
            resp.raise_for_status()
            payload = resp.json()
            if not payload:
                break
            for row in payload:
                filename = row.get("filename")
                if not filename:
                    continue
                entry = LoraEntry(
                    filename=filename,
                    name=row.get("name") or Path(filename).stem,
                    tags=row.get("tags") or "",
                    categories=list(row.get("categories") or []),
                )
                entries[filename] = entry
            if len(payload) < limit:
                break
            offset += limit
        return list(entries.values())

    def download_lora(self, entry: LoraEntry, target_dir: Path) -> Path:
        """Download the `.safetensors` file for ``entry`` into ``target_dir``."""

        target_dir.mkdir(parents=True, exist_ok=True)
        lora_path = target_dir / entry.filename
        resp = self.client.get(
            f"/uploads/{entry.filename}", headers={"Accept": "application/octet-stream"}
        )
        resp.raise_for_status()
        lora_path.write_bytes(resp.content)
        return lora_path

    def fetch_preview_urls(self, filename: str) -> list[str]:
        """Retrieve preview image URLs for ``filename`` by parsing the detail view."""

        resp = self.client.get(f"/detail/{filename}", headers={"Accept": "text/html"})
        if resp.status_code == 303:
            raise RuntimeError("Preview access denied – check permissions.")
        resp.raise_for_status()
        parser = PreviewImageParser()
        parser.feed(resp.text)
        return parser.urls

    def download_previews(self, urls: Iterable[str], target_dir: Path) -> list[Path]:
        """Download preview images referenced by ``urls`` into ``target_dir``."""

        target_dir.mkdir(parents=True, exist_ok=True)
        saved_paths: list[Path] = []
        for url in urls:
            absolute = urljoin(self.base_url + "/", url.lstrip("/"))
            filename = Path(url).name
            resp = self.client.get(absolute, headers={"Accept": "image/*"})
            if resp.status_code == 404:
                continue
            resp.raise_for_status()
            path = target_dir / filename
            path.write_bytes(resp.content)
            saved_paths.append(path)
        return saved_paths


def build_summary(entries: list[LoraEntry]) -> str:
    """Create a textual summary for the exported LoRAs."""

    lines = ["Exported LoRAs:"]
    for entry in sorted(entries, key=lambda e: e.name.lower()):
        lines.append(f"- {entry.name} ({entry.filename})")
        tags = entry.tags.strip() or "None"
        categories = entry.categories or ["No Category"]
        lines.append(f"  Tags: {tags}")
        lines.append(f"  Categories: {', '.join(categories)}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export LoRAs and previews from MyLora")
    parser.add_argument(
        "destination",
        type=Path,
        help="Target directory where the export should be stored",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    destination: Path = args.destination
    exporter = MyLoraExporter(MYLORA_HOST, MYLORA_USERNAME, MYLORA_PASSWORD)
    exporter.login()
    entries = exporter.fetch_entries()
    total_online = len(entries)
    successful: list[LoraEntry] = []

    for entry in entries:
        lora_dir = destination / entry.stem
        images_dir = lora_dir / f"{entry.stem}-Images"
        try:
            exporter.download_lora(entry, lora_dir)
            preview_urls = exporter.fetch_preview_urls(entry.filename)
            exporter.download_previews(preview_urls, images_dir)
            successful.append(entry)
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to export {entry.filename}: {exc}", file=sys.stderr)

    summary_text = build_summary(successful)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "exported_loras.txt").write_text(summary_text, encoding="utf-8")

    print(f"Loras Online in MyLora: {total_online}")
    print(f"Loras Offline exportiert: {len(successful)}")


if __name__ == "__main__":
    main()
