# PDF-Helper

import io
import os
import sys
from typing import Optional, Sequence, Collection
from pathlib import Path

import log21
import pypdfium2 as pdfium
from PIL import Image
from pypdfium2 import PdfImage, PdfBitmap, PdfDocument

__version__ = '0.2.1'

__all__ = [
    'bundle', 'merge_pdfs', 'remove_pages', 'pdf_to_image', 'extract_text',
    'image_to_pdf', 'split_pdf', 'watermark_pdf'
]


def bundle(
    input_files: Sequence[str | bytes | Path | os.PathLike[str] | io.BytesIO],
    output_stream: str | Path | io.BytesIO | io.BufferedWriter
) -> int:
    """Bundle multiple files together.

    :param input_files: List of files to bundle together. Each file can be a PDF or an
        image. Supported image formats are those supported by Pillow.
    :param output_stream: Output stream to write to.
    :return: Number of pages in the bundled PDF.
    """
    writer = PdfDocument.new()
    for input_file in input_files:
        log21.info(f'Adding {input_file}...')
        if isinstance(input_file, (str, bytes, Path, os.PathLike)):
            if str(input_file).lower().endswith('.pdf'):
                reader = PdfDocument(input_file)
                writer.import_pages(reader)
            else:
                image = Image.open(input_file)
                bitmap = PdfBitmap.from_pil(image)
                pdf_image = PdfImage.new(writer)
                pdf_image.set_bitmap(bitmap)
                matrix = pdfium.PdfMatrix().scale(bitmap.width, bitmap.height)
                pdf_image.set_matrix(matrix)
                page = writer.new_page(bitmap.width, bitmap.height)
                page.insert_obj(pdf_image)
                page.gen_content()
                page.close()
                pdf_image.close()
                bitmap.close()
                image.close()
        elif isinstance(input_file, io.BytesIO):
            try:
                reader = PdfDocument(input_file)
                writer.import_pages(reader)
            except Exception:
                image = Image.open(input_file)
                bitmap = PdfBitmap.from_pil(image)
                pdf_image = PdfImage.new(writer)
                pdf_image.set_bitmap(bitmap)
                matrix = pdfium.PdfMatrix().scale(bitmap.width, bitmap.height)
                pdf_image.set_matrix(matrix)
                page = writer.new_page(bitmap.width, bitmap.height)
                page.insert_obj(pdf_image)
                page.gen_content()
                page.close()
                pdf_image.close()
                bitmap.close()
                image.close()
        else:
            raise ValueError(f'Unsupported input file type: {type(input_file)}')
    writer.save(output_stream)
    return len(writer)


def merge_pdfs(
    input_files: Sequence[str | Path | io.TextIOWrapper],
    output_stream: str | Path | io.BytesIO | io.BufferedWriter
) -> int:
    """Merge PDF files.

    :param input_files: List of PDF files to concatenate.
    :param output_stream: Output stream to write to.
    :return: Number of pages of the merged PDF.
    """
    writer = PdfDocument.new()
    for input_file in input_files:
        log21.info(f'Adding {input_file}...')
        reader = PdfDocument(input_file)
        writer.import_pages(reader)
    writer.save(output_stream)
    return len(writer)


def image_to_pdf(
    input_files: Sequence[str | bytes | Path | os.PathLike[str] | io.BytesIO],
    output_stream: str | Path | io.BytesIO | io.BufferedWriter
) -> int:
    """Convert images to a PDF file.

    :param input_files: List of images to convert.
    :param output_stream: Output stream to write to.
    :return: Number of pages in the output PDF
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
    return len(writer)


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


def pdf_to_image(
    input_file: str | Path,
    output_directory: str | Path,
    pages_to_convert: Optional[Collection[int]] = None,
    scale: int = 2
) -> int:
    """Convert a PDF file to a series of images.

    :param input_file: PDF file to convert.
    :param output_directory: Directory to write images to.
    :param scale: Scale of each image.
    :return: Number of pages converted to image
    """
    if isinstance(input_file, str):
        input_file = Path(input_file)
    if isinstance(output_directory, str):
        output_directory = Path(output_directory)
    if not output_directory.exists():
        output_directory.mkdir(parents=True)

    pdf = pdfium.PdfDocument(input_file)
    name = input_file.name.rsplit('.', maxsplit=1)[0]
    # Number of digits each number in the filename should have
    length = len(str(len(pdf)))
    if not pages_to_convert:
        for i, page in enumerate(pdf, start=1):
            log21.info(f'Converting page {i}...', end='\r')
            image = page.render(scale=scale).to_pil()
            image.save(output_directory / f'{name}-{i:0>{length}}.png')
        return len(pdf)
    for i, page in enumerate(pdf, start=1):
        if i not in pages_to_convert:
            continue
        log21.info(f'Converting page {i}...', end='\r')
        image = page.render(scale=scale).to_pil()
        image.save(output_directory / f'{name}-{i:0>{length}}.png')
    return len(pages_to_convert)


def extract_text(
    input_file: str | Path | io.BytesIO | io.TextIOWrapper,
    pages_to_extract_from: Optional[Collection[int]] = None,
    max_number_of_characters: int = -1,
    reverse_lines: bool = False
) -> str:
    """Extract text from a PDF file.

    :param input_file: PDF file to extract text from.
    :param pages_to_extract_from: Pages to extract text from.
    :param max_number_of_characters: Maximum number of characters to extract in total.
    :param reverse_lines: Reverse the characters in each line (Useful for Persian text)
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
            text += page.get_textpage().get_text_range(count=count)
            if count == 0:
                break
            if count > 0:
                count = max_number_of_characters - len(text)
    else:
        count = max_number_of_characters
        for page in pdf:
            text += page.get_textpage().get_text_range(count=count)
            if count == 0:
                break
            if count > 0:
                count = max_number_of_characters - len(text)
            text += '\n'
    log21.info('\rDone!')

    if reverse_lines:
        reversed_text = ''
        log21.info('Reversing the lines...', end='\r')
        for i, line in enumerate(text.split(os.linesep), start=1):
            log21.info('Reversing line %d...', args=(i, ), end='\r')
            reversed_text += ''.join(reversed(line)) + os.linesep
        log21.info('\rReversed every line!')
        text = reversed_text

    return text


def split_pdf(
    input_file: str | Path,
    output_directory: str | Path,
    split_points: Optional[Collection[int]] = None
) -> int:
    """Split a PDF file into multiple files.

    :param input_file: PDF file to split.
    :param output_directory: Directory to write split files to.
    :param split_points: Pages to split. If None, splits every page into a separate
        file.
    :return: Number of pages split.
    """
    if isinstance(input_file, str):
        input_file = Path(input_file)
    if isinstance(output_directory, str):
        output_directory = Path(output_directory)
    if not output_directory.exists():
        output_directory.mkdir(parents=True)

    pdf = pdfium.PdfDocument(input_file)
    if not split_points:
        split_points = range(1, len(pdf) - 1)
    split_points = [0] + sorted(set(split_points)) + [len(pdf)]

    for i in range(len(split_points) - 1):
        start = split_points[i]
        end = split_points[i + 1]
        if start < 0 or end > len(pdf):
            log21.warning(
                f'Split points {start + 1} to {end} are out of bounds for '
                f'input file `{input_file}`.'
            )
            continue

        log21.info(f'Splitting pages {start + 1} to {end}...')
        writer = PdfDocument.new()
        writer.import_pages(pdf, range(start, end))
        output_file = output_directory / f'{input_file.stem}_part_{i + 1}.pdf'
        try:
            writer.save(output_file)
            log21.info(f'Saved split file to {output_file}')
        except PermissionError:
            log21.critical(
                f'Cannot write to output file `{output_file}`.\n'
                'Check the file permissions and close any applications that may be '
                'using the file, then try again.'
            )
            sys.exit(1)
        finally:
            writer.close()

    return len(split_points) - 1


def watermark_pdf(
    input_file: str | Path | io.BytesIO | io.TextIOWrapper,
    output_file: str | Path,
    watermark_text: str,
    position: str = 'center',
    font_size: int = 36,
    opacity: float = 0.1,
    rotation: float = 45.0
) -> int:
    """Split a PDF file into multiple files.

    :param input_file: PDF file to split.
    :param output_file:
    :param watermark_text: Text to use as watermark.
    :param position: Position of watermark. One of 'center' or '50% 50%', 'top-left' or
        '0% 0%', 'top-right' or '100% 0%', 'bottom-left' or '0% 100%', etc.
        You can also use absolute values like '100 100'.
        Note: The position is relative to the center of the watermark text.
    :param font_size: Font size of watermark text.
    :param opacity: Opacity of watermark text. Between 0.0 and 1.0.
    :param rotation: Rotation of watermark text in degrees.
    :return: Number of pages split.
    """
    if isinstance(input_file, str):
        input_file = Path(input_file)
    if isinstance(output_file, str):
        output_file = Path(output_file)
    if len(watermark_text) == 0:
        raise ValueError('Watermark text cannot be empty.')
    if font_size < 1:
        raise ValueError('Font size must be at least 1.')
    if opacity < 0.0 or opacity > 1.0:
        raise ValueError('Opacity must be between 0.0 and 1.0.')

    pdf = pdfium.PdfDocument(input_file)
    watermark = pdfium.PdfDocument.new()
    _page = watermark.new_page(512, 512)
    for i, _page in enumerate(pdf):
        log21.info(f'Adding watermark to page {i + 1}...', end='\r')
    log21.info('\rDone!')
    pdf.save(output_file)
    return len(pdf)
