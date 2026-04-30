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
+ [x] **Split PDFs**: Split a PDF into multiple PDFs, each containing a range of pages from
      the original PDF
+ [x] **Export as image**: Export designated pages from a PDF as image files
+ [x] **Remove pages**: Remove designated pages from a PDF
+ [ ] Encrypt a PDF
+ [ ] Decrypt a PDF
+ [ ] Add watermark to a PDF
+ [ ] Extract images from a PDF
+ [x] **Extract text**: Export text from a PDF file and optionally save it to a text file
+ [ ] Extract links from a PDF

If you want any other feature to be added, feel free to open an [issue](https://github.com/MPCodeWriter21/PDF-To-Image/issues)
or fork the repo and make a [pull request](https://github.com/MPCodeWriter21/PDF-To-Image/pulls)
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

# E.g. Merge PDFs 1, 2 and 3 into a new PDF
pdf-helper merge 1.pdf 2.pdf 3.pdf new.pdf

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
