# LoRA Database Web Interface

This project provides a minimal FastAPI application for organising LoRA files (`.safetensors`) along with preview images.  It allows uploading new LoRA models, automatically extracts their metadata and stores it in a small SQLite based search index.  A simple gallery interface lets you browse the models, search by name or tag and download or remove files.

## Preview
![grafik](https://github.com/user-attachments/assets/7dee8a00-085b-40f0-a545-9d171833e69b)

## Features

- **Upload LoRA files** – multiple `.safetensors` files can be uploaded at once.
- **Upload preview archives** – a ZIP file containing preview images is extracted and matched to the corresponding LoRA by filename.
- **Metadata extraction** – basic metadata is read from each safetensors file and stored in a full text search (FTS5) table.
- **Searchable gallery** – browse all indexed LoRAs in a grid view and filter by query.
- **Detail view** – see all previews, metadata and a download link for a single LoRA.
- **File removal** – delete LoRA files or individual preview images from the interface.

## Project layout

```
loradb/
├── agents/            # upload, metadata and search logic
├── api/               # FastAPI routes
├── static/            # CSS for the HTML templates
├── templates/         # Jinja2 templates for the web pages
├── uploads/           # stored LoRA files and preview images
└── search_index/      # SQLite database for the search index
main.py                # application entry point
config.py              # path configuration used by the app
requirements.txt       # Python dependencies
```

## Installation

Run the setup script directly from GitHub:

```bash
curl -sL https://raw.githubusercontent.com/AsaTyr2018/MyLora/main/setup.sh | sudo bash -s install
```

If you cloned the repository manually run:

```bash
sudo ./setup.sh install      # install
sudo ./setup.sh update       # update
sudo ./setup.sh uninstall    # remove
```

After installation the interface is available on [http://localhost:5000](http://localhost:5000).

## Usage

- **Upload models**: open `/upload` and select one or more `.safetensors` files.  Each file is stored in `loradb/uploads` and indexed automatically.
- **Upload previews**: open `/upload_previews` to upload a ZIP containing images.  Files named `mylora.png`, `mylora_1.png`, ... will be placed next to `mylora.safetensors` and shown in the gallery.
- **Browse and search**: the `/grid` page lists all indexed LoRAs. Use the search box to filter by filename or tags.
- **Detail view**: click a LoRA in the gallery to view all previews and metadata.  A download button is provided to retrieve the original file.
- **Delete files**: tick the checkboxes in the gallery or detail view and press *Remove Selected* to delete the chosen files.

The web pages use Bootstrap via a CDN and are rendered with Jinja2 templates.  The application keeps all data locally on disk in the `loradb` directory.

---

MIT License
