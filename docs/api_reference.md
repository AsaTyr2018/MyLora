# MyLora API Reference

This document provides an exhaustive reference for every HTTP endpoint exposed by MyLora.
All examples assume the service runs at `http://{serverip}:5000`.
Unless noted otherwise, responses are JSON objects and success is indicated with HTTP 200.

> **Tip:** Include `Accept: application/json` in your requests when you expect JSON output.
The web interface sends `Accept: text/html` to receive redirects or rendered templates instead.

## Authentication and Roles

MyLora uses session-based authentication backed by SQLite. Sessions are stored via FastAPI's
`SessionMiddleware` and optionally persisted with the `remember_user_id` cookie when "Remember me"
is selected during login.

| Role   | Description | Access level |
| ------ | ----------- | ------------ |
| `guest` | Unauthenticated visitor identified by the middleware. | Read-only showcase pages only. API calls are redirected (HTTP 303) to `/showcase`. |
| `user`  | Authenticated account created by an administrator. | Full read access to metadata and categories. Cannot perform administrative actions. |
| `admin` | Elevated account created via `usersetup.py` or the admin panel. | Full access including uploads, category maintenance, and user management. |

### Login Flow

1. **POST `/login`** – Submit the login form with `username`, `password`, and optional `save_account`.
   On success a server-side session is created and the browser receives a `remember_user_id` cookie if
   persistence was requested. On failure the page is re-rendered with HTTP 200 and an error message.
2. **GET `/logout`** – Clears the session and removes the `remember_user_id` cookie.

API clients should maintain the `session` cookie returned by FastAPI. Each subsequent request must include
this cookie to remain authenticated. Without it, the middleware treats the caller as `guest` and issues a
`303 See Other` redirect to `/showcase` for protected endpoints.

## Request Conventions

- **Base URL:** `http://{serverip}:5000`
- **Authentication:** Session cookie (see above). No token-based auth is currently provided.
- **Content types:** Multipart form uploads are used for file operations. JSON responses are returned by default.
- **Error format:** JSON objects with a `detail` field when FastAPI raises `HTTPException`.

## Endpoint Catalog

Endpoints are grouped by feature. Each table lists the primary success and error codes you may encounter.

### Search & Discovery

#### `GET /search`

| Requirement | Details |
| ----------- | ------- |
| Authorization | `user` or `admin` session. Guests receive `303 See Other` to `/showcase`. |
| Query Parameters | `query` (string, required), `limit` (int, optional), `offset` (int, default `0`). |
| Success Codes | `200 OK` with an array of metadata entries. |
| Error Codes | `422 Unprocessable Entity` for missing `query`, middleware `303 See Other` for guests. |

**Example**
```bash
curl -H "Accept: application/json" \
  "http://{serverip}:5000/search?query=lora&limit=10"
```

#### `GET /grid_data`

Returns metadata with category names and a randomly chosen preview URL.

| Requirement | Details |
| ----------- | ------- |
| Authorization | `user` or `admin`. Guests receive `303 See Other`. |
| Query Parameters | `q` (string, defaults to `*`), `category` (int, optional), `limit` (int, default `50`), `offset` (int, default `0`). |
| Success Codes | `200 OK`. |
| Error Codes | `422 Unprocessable Entity` for invalid parameter types, `303 See Other` for guests. |

**Example**
```bash
curl -H "Accept: application/json" \
  "http://{serverip}:5000/grid_data?q=portrait&limit=25"
```

#### `GET /showcase`

Public showcase HTML page listing models in the "Public viewing" category.

| Requirement | Details |
| ----------- | ------- |
| Authorization | Accessible to all roles including `guest`. |
| Success Codes | `200 OK` with HTML body. |

**Example**
```bash
curl -H "Accept: text/html" http://{serverip}:5000/showcase
```

#### `GET /showcase_detail/{filename}`

Guest-accessible detail page for a specific model.

| Requirement | Details |
| ----------- | ------- |
| Authorization | Accessible to all roles including `guest`. |
| Path Parameters | `filename` (string, required). |
| Success Codes | `200 OK` with HTML body. |

### Category Management

#### `GET /categories`

| Requirement | Details |
| ----------- | ------- |
| Authorization | `user` or `admin`. Guests receive `303 See Other`. |
| Success Codes | `200 OK` with an array of `{ "id": int, "name": str }`. |

**Example**
```bash
curl -H "Accept: application/json" http://{serverip}:5000/categories
```

#### `POST /categories`

Creates a new category.

| Requirement | Details |
| ----------- | ------- |
| Authorization | `admin`. Non-admin authenticated users receive `403 Forbidden` HTML. |
| Form Fields | `name` (string, required). |
| Success Codes | `200 OK` with `{ "id": int }`. |
| Error Codes | `303 See Other` redirect back to referrer for HTML submissions. |

**Example**
```bash
curl -X POST -H "Accept: application/json" \
  -F "name=Landscapes" http://{serverip}:5000/categories
```

#### `POST /assign_category`

Assigns a LoRA to a category.

| Requirement | Details |
| ----------- | ------- |
| Authorization | `admin`. |
| Form Fields | `filename` (string, required), `category_id` (int, required). |
| Success Codes | `200 OK` with `{ "status": "ok" }`. |
| Error Codes | `400 Bad Request` when the filename fails validation, `303 See Other` redirect for HTML. |

**Example**
```bash
curl -X POST -H "Accept: application/json" \
  -F "filename=awesome_lora.safetensors" \
  -F "category_id=3" http://{serverip}:5000/assign_category
```

#### `POST /assign_categories`

Assigns multiple LoRAs to an existing or newly created category.

| Requirement | Details |
| ----------- | ------- |
| Authorization | `admin`. |
| Form Fields | `files` (string list, at least one), `category_id` (int, optional), `new_category` (string, optional). One of `category_id` or `new_category` must be provided. |
| Success Codes | `200 OK` with `{ "status": "ok" }`. |
| Error Codes | `400 Bad Request` if no category was specified, `303 See Other` redirect for HTML. |

**Example**
```bash
curl -X POST -H "Accept: application/json" \
  -F "files=first.safetensors" \
  -F "files=second.safetensors" \
  -F "category_id=2" http://{serverip}:5000/assign_categories
```

#### `POST /unassign_category`

Removes a LoRA from a category.

| Requirement | Details |
| ----------- | ------- |
| Authorization | `admin`. |
| Form Fields | `filename` (string), `category_id` (int). |
| Success Codes | `200 OK` with `{ "status": "ok" }`. |
| Error Codes | `400 Bad Request` for invalid filenames, `303 See Other` redirect for HTML. |

#### `POST /delete_category`

Deletes a category.

| Requirement | Details |
| ----------- | ------- |
| Authorization | `admin`. |
| Form Fields | `category_id` (int, required). |
| Success Codes | `200 OK` with `{ "status": "ok" }`. |
| Error Codes | `303 See Other` redirect back to `/category_admin` for HTML submissions. |

### File Operations

#### `POST /upload`

Uploads one or more `.safetensors` model files.

| Requirement | Details |
| ----------- | ------- |
| Authorization | `admin`. |
| Form Fields | `files` (multipart file list, required). |
| Success Codes | `200 OK` with an array of extracted metadata objects. |
| Error Codes | `409 Conflict` if a file already exists, `400 Bad Request` for invalid filenames, `303 See Other` redirect to `/grid` when `Accept: text/html`. |

**Example**
```bash
curl -X POST -H "Accept: application/json" \
  -F "files=@awesome_lora.safetensors" http://{serverip}:5000/upload
```

#### `POST /upload_previews`

Uploads preview images or a ZIP archive.

| Requirement | Details |
| ----------- | ------- |
| Authorization | `admin`. |
| Form Fields | `files` (multipart file list, required), `lora` (string, optional unless uploading individual files). |
| Success Codes | `200 OK` with `{ "status": "ok" }`. |
| Error Codes | `200 OK` with `{ "error": "missing lora" }` if no target was provided, `303 See Other` redirect to `/grid` for HTML. |

#### `POST /delete`

Deletes LoRA or preview files.

| Requirement | Details |
| ----------- | ------- |
| Authorization | `admin`. |
| Form Fields | `files` (string list, required). |
| Success Codes | `200 OK` with `{ "deleted": [...] }`. |
| Error Codes | `303 See Other` redirect to `/grid` for HTML submissions. |

### User & Admin Interface

#### `GET /grid`

Renders the interactive gallery. Requires at least `user` role. Returns HTML with HTTP 200.

#### `GET /detail/{filename}`

Renders the detail view for a model. Requires `user` or `admin`. Returns HTML with HTTP 200, raises `404 Not Found` if the underlying file is missing.

#### `GET /category_admin`

Category administration dashboard. Requires `admin`. Returns HTML 200.

#### `POST /bulk_assign`

Renders the bulk assignment modal with the selected files and categories. Requires `admin`. Returns HTML 200.

#### `GET /admin/users`

Displays the user management dashboard. Requires `admin`. Returns HTML 200.

#### `POST /admin/users/add`

| Requirement | Details |
| ----------- | ------- |
| Authorization | `admin`. |
| Form Fields | `username` (string), `password` (string), `role` (string, defaults to `user`). |
| Success Codes | `200 OK` with `{ "status": "ok" }`. |
| Error Codes | `303 See Other` redirect to `/admin/users` for HTML submissions. |

#### `POST /admin/users/delete`

| Requirement | Details |
| ----------- | ------- |
| Authorization | `admin`. |
| Form Fields | `username` (string, required). |
| Success Codes | `200 OK` with `{ "status": "ok" }`. |
| Error Codes | `303 See Other` redirect to `/admin/users` for HTML submissions. |

## Error Handling Summary

- **303 See Other** – Returned by the authentication middleware when guests access protected endpoints, or by endpoints responding to HTML form submissions.
- **400 Bad Request** – Filename validation failures and missing category selections.
- **403 Forbidden** – Rendered HTML response when non-admin users attempt administrative endpoints.
- **404 Not Found** – Raised by `/detail/{filename}` when the LoRA file does not exist.
- **409 Conflict** – Attempt to upload a file that already exists.
- **422 Unprocessable Entity** – FastAPI validation errors for malformed parameters.

Ensure your client follows redirects and surfaces JSON error bodies where provided.
