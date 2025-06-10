#!/usr/bin python3

import io
import os
import sys
import importlib.util
from typing import Optional, Sequence, Collection
from pathlib import Path

import log21
import pypdfium2 as pdfium
from PIL import Image
from pypdfium2 import PdfImage, PdfBitmap, PdfDocument
from log21.Colors import RED, GREEN, RESET


def merge_pdfs(
    input_files: Sequence[str | Path | io.TextIOWrapper],
    output_stream: str | Path | io.BytesIO | io.BufferedWriter
):
    """Merge PDF files.

    :param input_files: List of PDF files to concatenate.
    :param output_stream: Output stream to write to.
    """
    writer = PdfDocument.new()
    for input_file in input_files:
        log21.info(f'Adding {input_file}...')
        reader = PdfDocument(input_file)
        writer.import_pages(reader)
    writer.save(output_stream)


def merge_pdfs_entry_point(
    input_paths: Sequence[Path],
    output_path: Path,
    /,
    force: bool = False,
    verbose: bool = False
):
    """Merge PDF files.

    :param output_path: Path to write concatenated PDF file to.
    :param input_paths: List of PDF files to concatenate.
    :param force: Force overwrite of output file.
    :param verbose: Print verbose output.
    """
    if len(input_paths) < 2:
        log21.critical('Must provide at least two input files.')
        sys.exit(1)
    if output_path.exists() and not force:
        log21.critical('Output file already exists.')
        sys.exit(1)
    if output_path.absolute() in (path.absolute() for path in input_paths):
        log21.critical('Input and output files cannot be the same.')
        sys.exit(1)
    if verbose:
        log21.basic_config(level=log21.INFO)

    for path in input_paths:
        if not path.exists():
            log21.critical(f'Input file `{path}` does not exist.')
            sys.exit(1)

    log21.info(f'Concatenating {len(input_paths)} files to {output_path}')
    try:
        with open(output_path, 'wb') as output_file:
            merge_pdfs(input_paths, output_file)
    except PermissionError:
        log21.critical(
            f'Cannot write to output file `{output_path}`.\n'
            'Check the file permissions and close any applications that may be using '
            'the file, then try again.'
        )
        sys.exit(1)


def remove_pages(
    input_file: str | Path | io.BytesIO | io.TextIOWrapper,
    pages_to_remove: Collection[int],
    output_stream: str | Path | io.BytesIO | io.BufferedWriter
) -> int:
    """Remove pages from a PDF file.

    :param input_file: PDF file to remove pages from.
    :param pages_to_remove: List of pages to remove. A one based collection of indices.
    :param output_stream: Output stream to write to.
    :return: Number of pages removed.
    """
    writer = PdfDocument.new()
    reader = PdfDocument(input_file)
    pages_to_remove = tuple((i - 1 for i in pages_to_remove))
    pages_to_add = [i for i in range(len(reader)) if i not in pages_to_remove]
    writer.import_pages(reader, pages_to_add)
    writer.save(output_stream, version=reader.get_version())
    return len(reader) - len(pages_to_add)


def parse_pages(pages: str):
    """Parses the pages string into a list of pages.

    :param pages: The pages string
        Example: '1-5,7,9-11'
    :return: A list of pages
        Example: [1, 2, 3, 4, 5, 7, 9, 10, 11]
    """
    pages_ = pages.replace(' ', '')
    pages_ = pages_.split(',')
    pages_ = [x.split('-') for x in pages_]
    pages_ = [x if len(x) == 1 else range(int(x[0]), int(x[1]) + 1) for x in pages_]
    pages_ = [int(x) for y in pages_ for x in y]
    return pages_


def remove_pages_entry_point(
    input_path: Path,
    output_path: Path,
    pages_to_remove: str,
    /,
    force: bool = False,
    verbose: bool = False
):
    """Remove pages from a PDF file.

    :param input_path: Path to PDF file to remove pages from.
    :param output_path: Path to write PDF file to.
    :param pages_to_remove: Comma-separated list of pages to remove.
        Example: '1-5,7,9-11'
    :param force: Force overwrite of output file.
    :param verbose: Print verbose output.
    """
    if not input_path.exists():
        log21.critical(f'Input file `{input_path}` does not exist.')
        sys.exit(1)
    if output_path.exists() and not force:
        log21.critical('Output file already exists.')
        sys.exit(1)
    if input_path.absolute() == output_path.absolute():
        log21.critical('Input and output files cannot be the same.')
        sys.exit(1)
    if verbose:
        log21.basic_config(level=log21.INFO)

    try:
        pages_to_remove_ = parse_pages(pages_to_remove)
    except ValueError:
        log21.critical(f'Invalid pages string: `{pages_to_remove}`')
        sys.exit(1)

    log21.info(
        f'Removing {len(pages_to_remove_)} page' + (
            's: ' + ', '.join(str(page) for page in pages_to_remove_[:-1]) +
            ' and' if len(pages_to_remove_) > 2 else ':'
        ) + f' {pages_to_remove_[-1]} from `{input_path}`'
    )
    try:
        with open(output_path, 'wb') as output_file:
            number_of_removed_pages = remove_pages(
                input_path, pages_to_remove_, output_file
            )
            log21.info(
                f'Removed {number_of_removed_pages} page' +
                ('s' if number_of_removed_pages > 1 else '') + '!'
            )
    except PermissionError:
        log21.critical(
            f'Cannot write to output file `{output_path}`.\n'
            'Check the file permissions and close any applications that may be using '
            'the file, then try again.'
        )
        sys.exit(1)


def pdf_to_image(
    input_file: str | Path,
    output_directory: str | Path,
    pages_to_convert: Optional[Collection[int]] = None,
    scale: int = 2
):
    """Convert a PDF file to a series of images.

    :param input_file: PDF file to convert.
    :param output_directory: Directory to write images to.
    :param scale: Scale of each image.
    """
    if isinstance(input_file, str):
        input_file = Path(input_file)
    if isinstance(output_directory, str):
        output_directory = Path(output_directory)
    if not output_directory.exists():
        output_directory.mkdir(parents=True)
    pdf = pdfium.PdfDocument(input_file)
    name = input_file.name.rsplit('.', maxsplit=1)[0]
    length = len(str(len(pdf)))
    if not pages_to_convert:
        for i, page in enumerate(pdf):
            i = i + 1
            log21.info(f'Converting page {i}...', end='\r')
            image = page.render(scale=scale).to_pil()
            image.save(output_directory / f'{name}-{i:0>{length}}.png')
    else:
        for i, page in enumerate(pdf):
            i = i + 1
            if i not in pages_to_convert:
                continue
            log21.info(f'Converting page {i}...', end='\r')
            image = page.render(scale=scale).to_pil()
            image.save(output_directory / f'{name}-{i:0>{length}}.png')


def pdf_to_image_entry_point(
    input_path: Path,
    output_directory: Path,
    /,
    pages_to_convert: Optional[str] = None,
    scale: int = 2,
    force: bool = False,
    verbose: bool = False
):
    """Convert a PDF file to a series of images.

    :param input_path: Path to PDF file to convert.
    :param output_directory: Path to directory to write images to.
    :param pages_to_convert: Comma-separated list of pages to convert.
        Example: '1-5,7,9-11'
    :param scale: Scale of each image.
    :param force: Force overwrite of output directory.
    :param verbose: Print verbose output.
    """
    if importlib.util.find_spec('PIL') is None:
        log21.error('PIL must be installed to use this feature.')
        cmd = 'python -m pip install "Pillow>=10.1.0"'
        answer = log21.input(
            f'[{RED}?{RESET}] Do you want to install it? ({GREEN}{cmd}{RESET})'
        )
        if answer.lower().startswith('y'):
            log21.print(f'[{GREEN}+{RESET}] Installing Pillow...')
            os.system(cmd)
        sys.exit(1)
    if not input_path.exists():
        log21.critical(f'Input file `{input_path}` does not exist.')
        sys.exit(1)
    if output_directory.exists() and not output_directory.is_dir():
        log21.critical(f'Output path `{output_directory}` is not a directory.')
        sys.exit(1)
    if output_directory.exists() and os.listdir(output_directory) and not force:
        log21.critical(f'Output directory `{output_directory}` already exists.')
        sys.exit(1)
    if verbose:
        log21.basic_config(level=log21.INFO)

    pages_to_convert_ = None
    if pages_to_convert:
        try:
            pages_to_convert_ = parse_pages(pages_to_convert)
        except ValueError:
            log21.critical(f'Invalid pages string: `{pages_to_convert}`')
            sys.exit(1)
        log21.info(
            f'Converting {len(pages_to_convert_)} page' +
            ('s' if len(pages_to_convert_) > 2 else '') +
            f' from `{input_path}` to image...'
        )
    else:
        log21.info(f'Converting `{input_path}` to images...')

    pdf_to_image(input_path, output_directory, pages_to_convert_, scale)
    log21.info('\rDone!')


def extract_text(
    input_file: str | Path | io.BytesIO | io.TextIOWrapper,
    pages_to_extract_from: Optional[Collection[int]] = None,
    max_number_of_characters: int = -1
) -> str:
    """Extract text from a PDF file.

    :param input_file: PDF file to extract text from.
    :param pages_to_extract_from: Pages to extract text from.
    :param max_number_of_characters: Maximum number of characters to extract in total.
    :return: Extracted text.
    """
    pdf = pdfium.PdfDocument(input_file)
    text = ''
    if pages_to_extract_from:
        pages_to_extract_from = sorted(pages_to_extract_from)
        if pages_to_extract_from[0] < 1:
            log21.critical('Pages must be >= 1')
            sys.exit(1)
        if pages_to_extract_from[-1] > len(pdf):
            log21.critical(
                f'Page {pages_to_extract_from[-1]} does not exist in `{input_file}`'
            )
            sys.exit(1)
        log21.info(
            f'Extracting text from {len(pages_to_extract_from)} page' +
            ('s' if len(pages_to_extract_from) > 1 else '') + f' from `{input_file}`...'
        )
        count = max_number_of_characters
        for i, page in enumerate(pdf):
            i = i + 1
            if i not in pages_to_extract_from:
                continue
            log21.info(f'Extracting text from page {i}...', end='\r')
            text += page.get_textpage().get_text_range(count=count, force_this=True)
            if count == 0:
                break
            if count > 0:
                count = max_number_of_characters - len(text)
    else:
        count = max_number_of_characters
        for page in pdf:
            text += page.get_textpage().get_text_range(count=count, force_this=True)
            if count == 0:
                break
            if count > 0:
                count = max_number_of_characters - len(text)
            text += '\n'
    log21.info('\rDone!')
    return text


def extract_text_entry_point(
    input_path: Path,
    /,
    output_path: Optional[Path] = None,
    pages_to_extract_from: Optional[str] = None,
    max_number_of_characters: int = -1,
    characters_to_split: int = 0,
    force: bool = False,
    verbose: bool = False
):
    """Extract text from a PDF file.

    :param input_path: Path to PDF file to extract text from.
    :param output_path: Path to write extracted text to. (Writes to stdout if not
        provided)
    :param pages_to_extract_from: Pages to extract text from. Example: '1-5,7,9-11'
    :param max_number_of_characters: Maximum number of characters to extract in total.
    :param characters_to_split: Create a new file if the number of characters in the
        extracted text exceeds this value.
    :param force: Force overwrite of output file.
    :param verbose: Print verbose output.
    """
    if not input_path.exists():
        log21.critical(f'Input file `{input_path}` does not exist.')
        sys.exit(1)
    if output_path and output_path.exists() and not force:
        log21.critical(f'Output `{output_path}` already exists.')
        sys.exit(1)
    if verbose:
        log21.basic_config(level=log21.INFO)

    pages_to_extract_from_ = None
    if pages_to_extract_from:
        try:
            pages_to_extract_from_ = parse_pages(pages_to_extract_from)
        except ValueError:
            log21.critical(f'Invalid pages string: `{pages_to_extract_from}`')
            sys.exit(1)
        log21.info(
            f'Extracting text from {len(pages_to_extract_from_)} page' +
            ('s' if len(pages_to_extract_from_) > 2 else '') +
            f' from `{input_path}`...'
        )
    else:
        log21.info(f'Extracting text from `{input_path}`...')

    text = extract_text(input_path, pages_to_extract_from_, max_number_of_characters)
    if output_path:
        if not characters_to_split:
            with output_path.open('w', encoding='utf-8') as file:
                file.write(text)
            return
        i = 1
        stem = output_path.stem
        while len(text) > characters_to_split:
            output_path_ = output_path.with_name(stem + f'_{i}{output_path.suffix}')
            with output_path_.open('w', encoding='utf-8') as file:
                file.write(text[:characters_to_split])
            text = text[characters_to_split:]
            output_path = output_path_
            i += 1
        with output_path.open('w', encoding='utf-8') as file:
            file.write(text)
    else:
        print(text)
    log21.info('\rDone!')


def image_to_pdf(
    input_files: Sequence[str | Path | io.TextIOWrapper],
    output_stream: str | Path | io.BytesIO | io.BufferedWriter
):
    """Convert images to a PDF file.

    :param input_files: List of images to convert.
    :param output_stream: Output stream to write to.
    """
    writer = PdfDocument.new()
    for input_file in input_files:
        log21.info(f'Adding {input_file}...')
        # Open the image file
        image = Image.open(input_file)
        # Create a bitmap from the image
        bitmap = PdfBitmap.from_pil(image)
        # Create a PdfImage object from the bitmap
        pdf_image = PdfImage.new(writer)
        pdf_image.set_bitmap(bitmap)
        matrix = pdfium.PdfMatrix().scale(bitmap.width, bitmap.height)
        pdf_image.set_matrix(matrix)
        # Create a new page and insert the PdfImage object
        page = writer.new_page(bitmap.width, bitmap.height)
        page.insert_obj(pdf_image)
        page.gen_content()
        # Close the objects
        page.close()
        pdf_image.close()
        bitmap.close()
        image.close()
    writer.save(output_stream)


def image_to_pdf_entry_point(
    input_paths: Sequence[Path],
    output_path: Path,
    /,
    force: bool = False,
    verbose: bool = False
):
    """Convert images to a PDF file.

    :param input_paths: List of images to convert.
    :param output_path: Path to write PDF file to.
    :param force: Force overwrite of output file.
    :param verbose: Print verbose output.
    """
    if len(input_paths) < 1:
        log21.critical('Must provide at least one input file.')
        sys.exit(1)
    if output_path.exists() and not force:
        log21.critical('Output file already exists.')
        sys.exit(1)
    if verbose:
        log21.basic_config(level=log21.INFO)

    for path in input_paths:
        if not path.exists():
            log21.critical(f'Input file `{path}` does not exist.')
            sys.exit(1)

    log21.info(f'Converting {len(input_paths)} images to `{output_path}`...')
    try:
        with open(output_path, 'wb') as output_file:
            image_to_pdf(input_paths, output_file)
    except PermissionError:
        log21.critical(
            f'Cannot write to output file `{output_path}`.\n'
            'Check the file permissions and close any applications that may be using '
            'the file, then try again.'
        )
        sys.exit(1)


if __name__ == '__main__':
    try:
        if sys.platform == 'win32':
            import msvcrt
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        log21.basic_config(level=log21.ERROR)
        log21.argumentify(
            {
                'merge': merge_pdfs_entry_point,
                'remove-pages': remove_pages_entry_point,
                'to-image': pdf_to_image_entry_point,
                'extract-text': extract_text_entry_point,
                'image-to-pdf': image_to_pdf_entry_point
            }
        )
    except KeyboardInterrupt:
        log21.critical('\nKeyboardInterrupt: Exiting...')
        sys.exit(1)
