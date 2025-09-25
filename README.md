[![MIT License](https://img.shields.io/github/license/AsaTyr2018/MyLora)](LICENSE)
[![Stars](https://img.shields.io/github/stars/AsaTyr2018/MyLora?style=social)](https://github.com/AsaTyr2018/MyLora/stargazers)
[![LoRAs Managed](https://img.shields.io/badge/LoRAs-Unlimited-purple?logo=fastapi)](https://github.com/AsaTyr2018/MyLora)
[![Featured on TurtlesAI](https://img.shields.io/badge/featured%20on-TurtlesAI-blueviolet?logo=readthedocs&logoColor=white)](https://www.turtlesai.com/en/pages-2946/mylora-intelligent-and-comprehensive-management-of)

# MyLora - One site to Rule them all!

MyLora provides a modern web interface to manage LoRA model files (`.safetensors`) alongside their preview images. The application is built with FastAPI and ships with a sleek dark mode interface.

# Proudly featured at TurtlesAI!
Link -> https://www.turtlesai.com/en/pages-2946/mylora-intelligent-and-comprehensive-management-of

## Highlights

- **Upload wizard** – drag & drop a LoRA file and its previews in one go.
- **Automatic metadata extraction** – tags, dimension and other information are parsed from the model files.
- **Searchable gallery** – browse all models, filter by tag or category and download directly.
- **User accounts** – login/logout with role-based permissions and secure session cookies.
- **Guest mode** – visitors are redirected to a public "Model Showcase" with preview-only details.
- **Category management** – create and assign categories with just a few clicks.
- **Bulk category assignment** – select multiple LoRAs in the gallery and add them to a category.
- **Local migration** – scripts are included to import existing collections or migrate old category files.
- **Admin tools** – manage users from the web UI and create the initial admin via `usersetup.py`.
- **Themed error pages** – friendly 404 page and access denied view.
- **Responsive design** – works great on desktop and mobile.

## Documentation

- [API usage overview](docs/api_usage.md) – quick start queries for automation scripts.
- [Detailed API reference](docs/api_reference.md) – authentication, inputs, and status codes for every endpoint.
- [Upload workflow guide](docs/upload_guide.md) – recommended process for preparing assets.

## Coming soon: Plugin support (Delayed)

MyLora is evolving into a modular platform!  
A full plugin system is being developed to allow custom extensions.

## Quick setup

Run the setup script directly from GitHub:

```bash
curl -sL https://raw.githubusercontent.com/AsaTyr2018/MyLora/main/setup.sh | sudo bash -s install
```

To update or remove an existing installation use:

```bash
sudo ./setup.sh update       # update
sudo ./setup.sh uninstall    # remove
```

The service will be available on [http://{serverip}:5000](http://{serverip}:5000).

## Admin User Setup (!Important!)

To set up the first admin user, run the following command in the root folder of the script:

```bash
python3 ./usersetup.py {user} {password}
```

### Docker builder

An alternative setup runs MyLora inside Docker. Execute the builder script and
start the created container:

```bash
cd docker_setup
python builder.py
cd app
docker compose up -d
```

To update the container later on, run `python update.py` from the same
directory.

## Pages overview

### Main site `/`
The landing page shows basic statistics and quick links to the gallery and the upload wizard.

![grafik](https://github.com/user-attachments/assets/41cdf81e-d71b-4c66-bbb2-22cbecfe8191)

### Gallery `/grid`
Grid view of all LoRAs with infinite scrolling, search box and category filter. Items link to their detail page.
![grafik](https://github.com/user-attachments/assets/278fd9dd-9a68-4def-8234-9920ed2d06a4)

### Detail view `/detail/<filename>`
Shows all preview images, extracted metadata and category management options for a single LoRA.

![grafik](https://github.com/user-attachments/assets/9db90546-bd4c-47f1-8eb0-dc66a1531849)

### Upload wizard `/upload_wizard`
Guided upload page that first asks for the `.safetensors` file and then its previews. Progress bars indicate upload status and the page redirects to the detail view when done.

![grafik](https://github.com/user-attachments/assets/30a14ca7-bd06-4af6-9e10-12a728b07c06)

### Category admin `/category_admin`
Manage all categories in one place. Create new entries and remove unused ones. A table lists how many LoRAs are assigned to each category.

![grafik](https://github.com/user-attachments/assets/28cfaab7-c6fc-471e-8ef1-87a21fcae47f)

## Bulk import
Use `bulk_import.py` to ingest an existing collection:

```bash
python bulk_import.py SAFETENSORS_DIR IMAGES_DIR [CATEGORIES_DIR]
```

## Offline export toolkit

Use `export_loras.py` to mirror all models, previews, and tags for offline use:

1. Either configure `MYLORA_HOST`, `MYLORA_USERNAME`, and `MYLORA_PASSWORD` at the top of the script **or** override them via command-line flags.
2. Run the exporter with the target directory for your archive. Adjust the timeout, retry behaviour, and batch size to match your server speed if necessary.

```bash
python export_loras.py /path/to/export \
  --host http://127.0.0.1:5000 \
  --username mylora_admin \
  --password secret \
  --timeout 60 \
  --retries 5 \
  --batch-size 250
```

The exporter walks the catalogue sequentially, requesting manageable batches so that thousands of LoRAs can be mirrored without keeping the entire listing in memory. Requests that run into read timeouts are retried using an exponential backoff, helping the process succeed even on slower connections. Each LoRA is stored in its own folder containing the `.safetensors` file and a `<name>-Images` subdirectory with previews. A generated `exported_loras.txt` lists every successfully exported model along with its tags and categories.

## Category migration
Convert old `<name>.txt` files in `loradb/uploads` to the new database format with:

```bash
python migrate_categories.py
```

---

MIT License
