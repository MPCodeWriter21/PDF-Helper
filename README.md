PDF-To-Image
============

A simple python script that helps with doing simple stuff with PDFs. It is going to
become a simple python package after `main.py` reaches 1000 lines of code.

Functionalities
---------------

+ [x] Merge PDFs
+ [ ] Split PDFs
+ [ ] Export PDF pages as image files
+ [x] Remove pages from a PDF
+ [ ] Encrypt a PDF
+ [ ] Decrypt a PDF
+ [ ] Add watermark to a PDF
+ [ ] Export images from a PDF
+ [ ] Export text from a PDF
+ [ ] Export links from a PDF

Usage
-----

### Install requirements

Install the most recent version of python for your operating system. Visit [python.org](https://python.org)

Use pip to install the dependencies:
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
