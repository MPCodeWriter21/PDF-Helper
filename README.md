PDF-Helper
==========

A simple python script that helps with doing simple stuff with PDFs. It is going to
become a simple python package after `main.py` reaches 1000 lines of code.

Features
--------

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
+ [x] **Image to PDF**: Export one or multiple images as a PDF file

If you want any other feature to be added, feel free to open an [issue](https://github.com/MPCodeWriter21/PDF-To-Image/issues)
or fork the repo and make a [pull request](https://github.com/MPCodeWriter21/PDF-To-Image/pulls)
after adding your contribution.

Usage
-----

### Install requirements

+ Install Python for your operating system. Visit [python.org](https://python.org)

+ Clone the repo:

```bash
git clone https://GitHub.com/MPCodeWriter21/PDF-Helper
```

+ Use pip to install the dependencies:

```bash
pip install -r requirements.txt
```

### Merge PDFs

Merge multiple PDFs into one PDF:

```bash
python3 main.py merge -i <input_file_1> <input_file_2>... <input_file_n> -o <output_file>

# E.g. Merge PDFs 1, 2 and 3 into a new PDF
python3 main.py merge -i 1.pdf 2.pdf 3.pdf -o new.pdf
```

### Split PDFs

Split a PDF into multiple PDFs, each containing a range of pages:

```bash
python3 main.py split -i <input_file> -o <output_folder> -s <split_point_1>,<split_point_2>

# E.g. Split a PDF into three PDFs, one with pages 1-10, the second with pages 11-20 and
# the third with pages 21-end
python3 main.py split -i my-pdf.pdf -o my-split-pdfs -s 10,20

# E.g. Split a PDF into PDFs each containing one page
python3 main.py split -i my-pdf.pdf -o my-split-pdfs  # No need to specify split points
```

### Export PDF pages as image files

Export PDF pages as image files:

```bash
python3 main.py to-image -i <input_file> -o <output_folder> \
        -p <page_number_1>,<page_number_2>,...,<page_number_n> -s <scale_factor>

# E.g. Export pages 1, 2, 3 and 6 from a PDF with scale factor 1
python3 main.py export-pages -i 1.pdf -o images -p 1-3,6 -s 1

# E.g. Export all pages from a PDF with scale 2
python3 main.py to-image -i my-pdf.pdf -o my-images
```

### Remove pages from a PDF

Remove pages from a PDF:

```bash
python3 main.py remove-pages -i <input_file> -o <output_file> -p <page_number_1>,<page_number_2>,...,<page_number_n>

# E.g. Remove pages 1, 2, 3 and 6 from a PDF
python3 main.py remove-pages -i 1.pdf -o new.pdf -p 1-3,6
```

### Export text from a PDF

To extract text from a PDF file and export them to text files you can do as follows:

```bash
python3 main.py extract-text -i <input_file> -o <output_file_name>

# E.g. Extract text from a PDF named my-pdf.pdf and save it to my-text.txt
python3 main.py extract-text -i my-pdf.pdf -o my-text.txt
```

### Export one or multiple images as a PDF file

You simply provide the script with your images, and it will create a PDF file with them:

```bash
python3 main.py image-to-pdf -i <image_1> <image_2> <image_3> ... -o <output_file>

# E.g. Take 1.png, 2.jpg, and 3.png and create a PDF named 123.pdf and override
# if already exists
python3 main.py -i 1.png 2.jpg 3.png -o 123.pdf -f
```

About
-----

Author: [CodeWriter21](https://github.com/MPCodeWriter21)

GitHub: [MPCodeWriter21/PDF-To-Image](https://github.com/MPCodeWriter21/PDF-To-Image)

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
