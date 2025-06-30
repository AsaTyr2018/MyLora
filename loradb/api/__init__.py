from fastapi import APIRouter, UploadFile, File, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path
import random
import re

import config

from ..agents.uploader_agent import UploaderAgent
from ..agents.metadata_extractor_agent import MetadataExtractorAgent
from ..agents.indexing_agent import IndexingAgent
from ..agents.frontend_agent import FrontendAgent

router = APIRouter()

uploader = UploaderAgent()
extractor = MetadataExtractorAgent()
indexer = IndexingAgent()
frontend = FrontendAgent(Path(uploader.upload_dir), Path(config.TEMPLATE_DIR))
uploader.frontend = frontend

# Regular expression for valid LoRA filenames. Only allow alphanumerics,
# dashes and underscores ending with the ``.safetensors`` extension. This
# prevents path traversal and protocol injections in redirect URLs.
_SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9_.-]+\.safetensors$", re.ASCII)


def _validate_filename(filename: str) -> str:
    """Return ``filename`` if it looks safe, otherwise raise ``HTTPException``."""
    cleaned = Path(filename).name
    if cleaned != filename or cleaned.startswith('.'):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not _SAFE_FILENAME_RE.fullmatch(cleaned):
        raise HTTPException(status_code=400, detail="Invalid filename")
    return cleaned


@router.get('/upload', response_class=HTMLResponse)
async def upload_form():
    """Render HTML form for file uploads."""
    return frontend.env.get_template('upload.html').render(title='Upload')

@router.get('/upload_wizard', response_class=HTMLResponse)
async def upload_wizard_form():
    """Combined upload form for LoRA and previews."""
    return frontend.env.get_template('upload_wizard.html').render(title='Upload Wizard')

@router.post('/upload')
async def upload(request: Request, files: list[UploadFile] = File(...)):
    saved_paths = uploader.save_files(files)
    results = []
    for path in saved_paths:
        meta = extractor.extract(Path(path))
        indexer.add_metadata(meta)
        results.append(meta)
    # HTML uploads redirect to gallery
    if 'text/html' in request.headers.get('accept', ''):
        return RedirectResponse(url='/grid', status_code=303)
    return results


@router.get('/upload_previews', response_class=HTMLResponse)
async def upload_previews_form(lora: str | None = None):
    """Form for uploading preview images or zip files.

    If ``lora`` is provided, the form will target that specific LoRA and allow
    uploading additional preview images. Otherwise a generic upload form for a
    preview ZIP is shown.
    """
    template = frontend.env.get_template('upload_previews.html')
    return template.render(title='Upload Previews', lora=lora)


@router.post('/upload_previews')
async def upload_previews(
    request: Request,
    files: list[UploadFile] = File(...),
    lora: str | None = Form(None),
):
    if len(files) == 1 and files[0].filename.lower().endswith('.zip') and lora is None:
        stem = Path(files[0].filename).stem
        uploader.save_preview_zip(files[0])
    else:
        if not lora:
            return {"error": "missing lora"}
        stem = lora
        uploader.save_preview_files(stem, files)
    frontend.refresh_preview_cache(stem)
    if 'text/html' in request.headers.get('accept', ''):
        return RedirectResponse(url='/grid', status_code=303)
    return {"status": "ok"}

@router.get('/search')
async def search(query: str, limit: int | None = None, offset: int = 0):
    return indexer.search(query, limit=limit, offset=offset)

@router.get('/grid_data')
async def grid_data(q: str = '*', category: int | None = None, offset: int = 0, limit: int = 50):
    if not q:
        q = '*'
    if category:
        entries = indexer.search_by_category(category, q, limit=limit, offset=offset)
    else:
        entries = indexer.search(q, limit=limit, offset=offset)
    for e in entries:
        e['categories'] = indexer.get_categories_for(e['filename'])
        stem = Path(e.get('filename', '')).stem
        previews = frontend._find_previews(stem)
        e['preview_url'] = random.choice(previews) if previews else None
    return entries


@router.get('/categories')
async def list_categories():
    return indexer.list_categories()


@router.post('/categories')
async def create_category(request: Request, name: str = Form(...)):
    """Create a new category and optionally redirect for HTML forms."""
    cid = indexer.create_category(name)
    if 'text/html' in request.headers.get('accept', ''):
        referer = request.headers.get('referer', '/grid')
        return RedirectResponse(url=referer, status_code=303)
    return {'id': cid}


@router.post('/assign_category')
async def assign_category(request: Request, filename: str = Form(...), category_id: int = Form(...)):
    fname = _validate_filename(filename)
    indexer.assign_category(fname, category_id)
    if 'text/html' in request.headers.get('accept', ''):
        return RedirectResponse(url=f'/detail/{fname}', status_code=303)
    return {'status': 'ok'}


@router.post('/unassign_category')
async def unassign_category(request: Request, filename: str = Form(...), category_id: int = Form(...)):
    """Remove ``filename`` from the given ``category_id``."""
    fname = _validate_filename(filename)
    indexer.unassign_category(fname, category_id)
    if 'text/html' in request.headers.get('accept', ''):
        return RedirectResponse(url=f'/detail/{fname}', status_code=303)
    return {'status': 'ok'}


@router.get('/category_admin', response_class=HTMLResponse)
async def category_admin():
    """Display the category administration page."""
    categories = indexer.list_categories_with_counts()
    return frontend.render_category_admin(categories)


@router.post('/delete_category')
async def delete_category(request: Request, category_id: int = Form(...)):
    indexer.delete_category(category_id)
    if 'text/html' in request.headers.get('accept', ''):
        referer = request.headers.get('referer', '/category_admin')
        return RedirectResponse(url=referer, status_code=303)
    return {'status': 'ok'}

@router.get('/grid', response_class=HTMLResponse)
async def grid(request: Request):
    query = request.query_params.get('q', '*')
    if not query:
        query = '*'
    category = request.query_params.get('category')
    limit = int(request.query_params.get('limit', 50))
    offset = int(request.query_params.get('offset', 0))
    categories = indexer.list_categories()
    if category:
        entries = indexer.search_by_category(int(category), query, limit=limit, offset=offset)
    else:
        entries = indexer.search(query, limit=limit, offset=offset)
    for e in entries:
        e['categories'] = indexer.get_categories_for(e['filename'])
    return frontend.render_grid(
        entries,
        query=query if query != '*' else '',
        categories=categories,
        selected_category=category or '',
        limit=limit,
    )


@router.get('/detail/{filename}', response_class=HTMLResponse)
async def detail(filename: str):
    results = indexer.search(f'"{filename}"')
    entry = results[0] if results else {"filename": filename}
    meta = extractor.extract(Path(uploader.upload_dir) / filename)
    entry["metadata"] = meta
    entry["categories"] = indexer.get_categories_with_ids(filename)
    categories = indexer.list_categories()
    return frontend.render_detail(entry, categories=categories)


@router.post('/delete')
async def delete_files(request: Request):
    """Delete selected LoRA or preview files."""
    form = await request.form()
    files = form.getlist('files')
    deleted = []
    for fname in files:
        if fname.endswith('.safetensors'):
            uploader.delete_lora(fname)
            indexer.remove_metadata(fname)
        else:
            uploader.delete_preview(fname)
        frontend.invalidate_preview_cache(Path(fname).stem)
        deleted.append(fname)
    if 'text/html' in request.headers.get('accept', ''):
        return RedirectResponse(url='/grid', status_code=303)
    return {'deleted': deleted}
