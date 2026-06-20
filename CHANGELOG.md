Changelog
=========

All notable changes to PDF-Helper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

[0.3.0]
-------

### Added

- Recipe system: run multi-step PDF workflows from YAML files
  - 8 supported operations: `bundle`, `remove_pages`, `split_pdf`, `pdf_to_image`,
    `extract_text`, `watermark`, `encrypt`, `metadata`
  - Step referencing with `input: { step: step_id }` to pipe outputs
  - Template resolution (`{temp_dir}`) in file paths
  - Input resolution from environment variables or interactive prompts
  - Cleanup of temporary files via `cleanup_temp` setting
- New CLI subcommand: `pdf-helper run-recipe <recipe.yaml> [--force] [--verbose]`
- `encrypt_pdf()` and `set_metadata()` API functions (raise `NotImplementedError`,
  graceful pipeline fallback)
- Example recipes in `examples/recipes/`:
  - `remove-pages.yaml` — remove pages from a PDF
  - `bundle-with-pages.yaml` — bundle files with per-file page selection
  - `split-convert-extract.yaml` — split, convert to images, and extract text
  - `secure-report-workflow.yaml` — full multi-step pipeline with encryption and metadata
- Recipe JSON Schema at `schemas/recipe-schema.json` for YAML LSP support

### Fixed

- Windows file-lock issues: explicit `PdfDocument` reader/writer close in `bundle()`,
  `remove_pages()`, and `split_pdf()`
- README: corrected `merge` CLI example to `bundle`
