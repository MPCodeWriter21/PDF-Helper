PDF-Helper
==========

A simple python package that helps with doing simple stuff with PDFs.

Features
--------

+ [x] **Bundle**: Bundle multiple files into one PDF
  + [x] PDF inputs
  + [x] Image inputs (e.g. PNG, JPG, etc.)
  + [ ] Markdown inputs
+ [x] **Merge PDFs**: Merge multiple PDFs into one PDF
+ [x] **Split PDFs**: Split a PDF into multiple PDFs, each containing a range of pages
+ [x] **Export as image**: Export designated pages from a PDF as image files
+ [x] **Remove pages**: Remove designated pages from a PDF
+ [x] **Extract text**: Export text from a PDF file and optionally save it to a text file
+ [x] **Recipe system**: Chain multiple operations together using YAML recipe files
+ [ ] Add watermark to a PDF
+ [ ] Encrypt a PDF
+ [ ] Decrypt a PDF
+ [ ] Extract images from a PDF
+ [ ] Extract links from a PDF
+ [ ] Set PDF metadata (title, author, etc.)

If you want any other feature to be added, feel free to open an [issue](https://github.com/MPCodeWriter21/PDF-Helper/issues)
or fork the repo and make a [pull request](https://github.com/MPCodeWriter21/PDF-Helper/pulls)
after adding your contribution.

Usage
-----

### Installation

You can install PDF-Helper via pip:

```bash
pip install pdf-helper

# Or use uv to install the tool
uv tool install pdf-helper
```

And run it using the command line:

```bash
pdf-helper <command> [options]
```

Or you can use uvx to run the package without installing it in a specific python environment:

```bash
uvx pdf-helper <command> [options]
```

You can also clone the repository and use `uv run`:

```bash
git clone https://github.com/MPCodeWriter21/PDF-Helper.git
cd PDF-Helper
uv run pdf-helper <command> [options]
```

### Bundle PDFs

Bundle multiple files into one PDF:

```bash
pdf-helper bundle <input_file_1> <input_file_2>... <input_file_n> <output_file>

# E.g. Bundle PDFs 1, 2 and 3 into a new PDF
pdf-helper bundle 1.pdf 2.pdf 3.pdf new.pdf

# E.g. Take 1.png, 2.jpg, and 3.png and create a PDF named 123.pdf and override
# if already exists
pdf-helper bundle 1.png 2.jpg 3.png 123.pdf -f

# E.g. Take part1.pdf, image1.png, ending.pdf and bundle them into a PDF named final.pdf
pdf-helper bundle part1.pdf image1.png ending.pdf final.pdf -v
```

### Split PDFs

Split a PDF into multiple PDFs, each containing a range of pages:

```bash
pdf-helper split <input_file> <output_folder> -s <split_point_1>,<split_point_2>

# E.g. Split a PDF into three PDFs, one with pages 1-10, the second with pages 11-20 and
# the third with pages 21-end
pdf-helper split my-pdf.pdf my-split-pdfs -s 10,20

# E.g. Split a PDF into PDFs each containing one page
pdf-helper split my-pdf.pdf my-split-pdfs  # No need to specify split points
```

### Export PDF pages as image files

Export PDF pages as image files:

```bash
pdf-helper to-image <input_file> <output_folder> \
        -p <page_number_1>,<page_number_2>,...,<page_number_n> -s <scale_factor>

# E.g. Export pages 1, 2, 3 and 6 from a PDF with scale factor 1
pdf-helper to-image 1.pdf images -p 1-3,6 -s 1

# E.g. Export all pages from a PDF with scale 2
pdf-helper to-image my-pdf.pdf my-images
```

### Remove pages from a PDF

Remove pages from a PDF:

```bash
pdf-helper remove-pages <input_file> <output_file> <page_number_1>,<page_number_2>,...,<page_number_n>

# E.g. Remove pages 1, 2, 3 and 6 from a PDF
pdf-helper remove-pages 1.pdf new.pdf 1-3,6
```

### Export text from a PDF

To extract text from a PDF file and export them to text files you can do as follows:

```bash
pdf-helper extract-text <input_file> -o <output_file_name>

# E.g. Extract text from a PDF named my-pdf.pdf and save it to my-text.txt
pdf-helper extract-text my-pdf.pdf -o my-text.txt
```

### Run Recipes

The recipe system lets you chain multiple PDF operations together in a single run
using a YAML file. This unlocks features not available through individual CLI
commands (e.g. selecting specific pages per file when bundling).

```bash
pdf-helper run-recipe <recipe_file.yaml>

# E.g. Run a simple recipe
pdf-helper run-recipe remove-pages.yaml

# E.g. Run with force overwrite and verbose logging
pdf-helper run-recipe bundle-workflow.yaml --force --verbose
```

#### Recipe File Format

A recipe is a YAML file with a `steps` list. Each step has an `id`, an
`operation`, input/output paths, and operation-specific options. Steps can
reference each other's outputs using `{ step: step_id }`.

```yaml
name: "Remove specific pages"
description: "Removes pages 2, 4, 6 from a PDF."
version: "1.0"

steps:
  - id: clean
    operation: remove_pages
    input: document.pdf
    pages_to_remove: [2, 4, 6]
    output: cleaned.pdf
```

#### Supported Operations

| Operation | Status | Description |
|---|---|---|
| `bundle` | Available | Bundle files with optional per-file page selection |
| `remove_pages` | Available | Remove pages by 1-based index |
| `split_pdf` | Available | Split at given page boundaries |
| `pdf_to_image` | Available | Render pages as PNG images |
| `extract_text` | Available | Extract text content |
| `watermark` | Planned | Add text watermark (graceful fallback) |
| `encrypt` | Planned | Password-protect PDF (graceful fallback) |
| `metadata` | Planned | Set title/author/keywords (graceful fallback) |

Operations marked *Planned* are not yet implemented — the recipe runner
logs a warning and copies the input file through, so pipelines don't break.

#### Advanced Example: Multi-step Pipeline

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/MPCodeWriter21/PDF-Helper/master/schemas/recipe-schema.json
name: "Split, Convert, and Extract Pipeline"
version: "1.0"

settings:
  temp_dir: "./.recipe-tmp"

steps:
  # Step 1: Split the PDF at pages 5 and 10
  - id: split
    operation: split_pdf
    input: report.pdf
    split_points: [5, 10]
    output_dir: .
    output_prefix: "report_part_"

  # Step 2: Convert the second chunk to images
  - id: to_images
    operation: pdf_to_image
    input:
      step: split
      file: report_part_2.pdf
    pages: "1-3"
    scale: 3
    output: ./output/images

  # Step 3: Extract text from the first chunk
  - id: extract
    operation: extract_text
    input:
      step: split
      file: report_part_1.pdf
    pages: "1-4"
    max_characters: 5000
    reverse_lines: true
    output: ./output/chapter-1-text.txt
```

#### Recipe Settings

| Setting | Default | Description |
|---|---|---|
| `temp_dir` | `./.recipe-tmp` | Directory for intermediate files |
| `overwrite` | `false` | Overwrite existing output files |
| `cleanup_temp` | `false` | Remove temp directory after completion |

Input values (e.g. passwords) can be sourced from environment variables or
prompted at runtime:

```yaml
inputs:
  password:
    env: PDF_PASSWORD
    prompt: "Enter output PDF password"
```

See [`examples/recipes/`](examples/recipes) for more example recipe files.

About
-----

Author: [CodeWriter21](https://github.com/MPCodeWriter21)

GitHub: [MPCodeWriter21/PDF-Helper](https://github.com/MPCodeWriter21/PDF-Helper)

Donations
---------

Your donations are very welcome: [nowpayments.io](https://nowpayments.io/donation/MehradP21)

You can also consider donating a
[Star](https://github.com/MPCodeWriter21/PDF-Helper) to the repo.

License
-------

This project is licensed under the MIT License.

See the [LICENSE](LICENSE)

References
----------

+ [pypdfium2](https://pypdfium2.readthedocs.io/en/stable/readme.html)
+ [PILlow](https://pillow.readthedocs.io/en/stable/)
+ [log21](https://GitHub.com/MPCodeWriter21/log21)
