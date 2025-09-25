"""MyLora export utility.

Download LoRA models along with their preview images from a running MyLora
instance and organise them into a structured folder layout for offline use.
"""

from __future__ import annotations

import argparse
import sys
import time
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

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        *,
        timeout: float = 30.0,
        retries: int = 3,
        retry_backoff: float = 2.0,
    ) -> None:
        if not base_url:
            raise ValueError("MYLORA_HOST is not configured")
        if retries < 1:
            raise ValueError("retries must be at least 1")
        if timeout <= 0:
            raise ValueError("timeout must be greater than 0")
        if retry_backoff < 1.0:
            raise ValueError("retry_backoff must be >= 1.0")

        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.retries = retries
        self.retry_backoff = retry_backoff
        timeout_config = httpx.Timeout(timeout, connect=timeout, read=timeout, write=timeout)
        self.client = httpx.Client(
            base_url=self.base_url, follow_redirects=False, timeout=timeout_config
        )

    def _get_with_retry(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, object] | None = None,
    ) -> httpx.Response:
        """Issue a GET request and retry on read timeouts."""

        last_exception: httpx.ReadTimeout | None = None
        for attempt in range(1, self.retries + 1):
            try:
                return self.client.get(url, headers=headers, params=params)
            except httpx.ReadTimeout as exc:
                last_exception = exc
                if attempt == self.retries:
                    break
                wait_time = self.retry_backoff ** (attempt - 1)
                time.sleep(wait_time)

        raise RuntimeError(
            f"Request to {url} timed out after {self.retries} attempts"
        ) from last_exception

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

    def iter_entries(self, limit: int = 100) -> Iterable[LoraEntry]:
        """Yield LoRA entries in batches to avoid loading the full catalogue."""

        if limit < 1:
            raise ValueError("limit must be at least 1")

        seen: set[str] = set()
        offset = 0
        while True:
            resp = self._get_with_retry(
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
                if filename in seen:
                    continue
                entry = LoraEntry(
                    filename=filename,
                    name=row.get("name") or Path(filename).stem,
                    tags=row.get("tags") or "",
                    categories=list(row.get("categories") or []),
                )
                seen.add(filename)
                yield entry
            if len(payload) < limit:
                break
            offset += limit

    def fetch_entries(self, limit: int = 100) -> list[LoraEntry]:
        """Return all LoRA entries available in MyLora."""

        return list(self.iter_entries(limit=limit))

    def download_lora(self, entry: LoraEntry, target_dir: Path) -> Path:
        """Download the `.safetensors` file for ``entry`` into ``target_dir``."""

        target_dir.mkdir(parents=True, exist_ok=True)
        lora_path = target_dir / entry.filename
        resp = self._get_with_retry(
            f"/uploads/{entry.filename}",
            headers={"Accept": "application/octet-stream"},
        )
        resp.raise_for_status()
        lora_path.write_bytes(resp.content)
        return lora_path

    def fetch_preview_urls(self, filename: str) -> list[str]:
        """Retrieve preview image URLs for ``filename`` by parsing the detail view."""

        resp = self._get_with_retry(f"/detail/{filename}", headers={"Accept": "text/html"})
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
            resp = self._get_with_retry(absolute, headers={"Accept": "image/*"})
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
    parser.add_argument(
        "--host",
        default=MYLORA_HOST,
        help="MyLora base URL (defaults to MYLORA_HOST)",
    )
    parser.add_argument(
        "--username",
        default=MYLORA_USERNAME,
        help="MyLora username (defaults to MYLORA_USERNAME)",
    )
    parser.add_argument(
        "--password",
        default=MYLORA_PASSWORD,
        help="MyLora password (defaults to MYLORA_PASSWORD)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout in seconds for HTTP requests (default: 30)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of retry attempts when a request times out (default: 3)",
    )
    parser.add_argument(
        "--retry-backoff",
        type=float,
        default=2.0,
        help="Exponential backoff factor between retries (default: 2.0)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of entries to request per batch during export (default: 100)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    destination: Path = args.destination
    exporter = MyLoraExporter(
        args.host,
        args.username,
        args.password,
        timeout=args.timeout,
        retries=args.retries,
        retry_backoff=args.retry_backoff,
    )
    exporter.login()
    successful: list[LoraEntry] = []
    total_online = 0

    for entry in exporter.iter_entries(limit=args.batch_size):
        total_online += 1
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
