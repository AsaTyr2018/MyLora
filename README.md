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
- **Category management** – create and assign categories with just a few clicks.
- **Bulk category assignment** – select multiple LoRAs in the gallery and add them to a category.
- **Local migration** – scripts are included to import existing collections or migrate old category files.
- **Responsive design** – works great on desktop and mobile.

## Coming soon: Plugin support 

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

## Category migration
Convert old `<name>.txt` files in `loradb/uploads` to the new database format with:

```bash
python migrate_categories.py
```

---

MIT License
