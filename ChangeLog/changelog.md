# Changelog

1. [Addition] Detailed API reference documentation
   - General Description: Added a comprehensive API reference covering authentication, request inputs, and response codes.
   - Technical Changes: Created `docs/api_reference.md` and linked it from the README documentation section.
   - Data Changes: Introduced a documentation directory entry and ensured the README navigation reflects the new material.
2. [Addition] Offline export automation
   - General Description: Delivered a command-line exporter that mirrors all online LoRAs, their previews, and metadata for offline archives.
   - Technical Changes: Added `export_loras.py` with authentication-aware downloads and updated the README with usage instructions.
   - Data Changes: Documented the generated `exported_loras.txt` report that captures exported LoRA names with associated tags and categories.
3. [Fix] Hardened offline exporter against slow responses
   - General Description: Resolved timeouts encountered when exporting from slower or remote MyLora instances by making the HTTP client more resilient.
   - Technical Changes: Introduced configurable request timeouts, retry logic with exponential backoff, and CLI flags to override connection settings.
   - Data Changes: Updated README guidance to document the new exporter options and behaviour.
4. [Fix] Sequential offline export pagination
   - General Description: Prevented the exporter from loading thousands of LoRAs into memory at once by iterating through the catalogue in batches.
   - Technical Changes: Added a streaming `iter_entries` helper, a configurable batch size flag, and sequential counting to keep the process responsive for very large datasets.
   - Data Changes: Documented the sequential export behaviour and batch tuning guidance in the README.
