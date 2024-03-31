PDF-To-Image
============

A simple python script that helps with doing simple stuff with PDFs. It is going to
become a simple python package after `main.py` reaches 1000 lines of code.

Features
--------

+ [x] Merge PDFs
+ [ ] Split PDFs
+ [x] Export PDF pages as image files
+ [x] Remove pages from a PDF
+ [ ] Encrypt a PDF
+ [ ] Decrypt a PDF
+ [ ] Add watermark to a PDF
+ [ ] Export images from a PDF
+ [ ] Export text from a PDF
+ [ ] Export links from a PDF

If you want any other feature to be added, feel free to open an [issue](https://github.com/MPCodeWriter21/PDF-To-Image/issues)
or fork the repo and make a [pull request](https://github.com/MPCodeWriter21/PDF-To-Image/pulls)
after adding your contribution.

Usage
-----

### Install requirements

+ Install the most recent version of python for your operating system. Visit [python.org](https://python.org)

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


### Export PDF pages as image files

Export PDF pages as image files:
```bash
python3 main.py export-pages -i <input_file> -o <output_folder> -p <page_number_1>,<page_number_2>,...,<page_number_n> -s <scale_factor>

# E.g. Export pages 1, 2, 3 and 6 from a PDF with scale factor 1
python3 main.py export-pages -i 1.pdf -o images -p 1-3,6 -s 1

# E.g. Export all pages from a PDF with scale 2
python3 main.py export-pages -i my-pdf.pdf -o my-images
```

### Remove pages from a PDF

Remove pages from a PDF:
```bash
python3 main.py remove-pages -i <input_file> -o <output_file> -p <page_number_1>,<page_number_2>,...,<page_number_n>

# E.g. Remove pages 1, 2, 3 and 6 from a PDF
python3 main.py remove-pages -i 1.pdf -o new.pdf -p 1-3,6
```

About
-----

Author: [CodeWriter21](https://github.com/MPCodeWriter21)

GitHub: [MPCodeWriter21/PDF-To-Image](https://github.com/MPCodeWriter21/PDF-To-Image)

License
-------

This project is licensed under the MIT License.

see the [LICENSE](LICENSE)
