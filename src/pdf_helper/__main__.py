#!/usr/bin/env python3

# yapf: disable

import os
import sys
import importlib.util
from typing import Optional, Sequence
from pathlib import Path

import log21
from log21.colors import RED, GREEN, RESET

from . import bundle, split_pdf, extract_text, pdf_to_image, remove_pages, watermark_pdf
from .utils import parse_pages

# yapf: ensable


def bundle_entry_point(
    input_paths: Sequence[Path],
    output_path: Path,
    /,
    force: bool = False,
    verbose: bool = False
) -> None:
    """Bundle multiple files into a single PDF file.

    :param input_paths: List of files to bundle. Can be PDF or image files.
    :param output_path: Path to write bundled PDF file to.
    :param force: Force overwrite of output file.
    :param verbose: Print verbose output.
    """
    if len(input_paths) < 1:
        log21.critical('Must provide at least one input file.')
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

    log21.info(f'Bundling {len(input_paths)} files to {output_path}...')
    try:
        with open(output_path, 'wb') as output_file:
            bundle(input_paths, output_file)
    except PermissionError:
        log21.critical(
            f'Cannot write to output file `{output_path}`.\n'
            'Check the file permissions and close any applications that may be using '
            'the file, then try again.'
        )
        sys.exit(1)


def remove_pages_entry_point(
    input_path: Path,
    output_path: Path,
    pages_to_remove: str,
    /,
    force: bool = False,
    verbose: bool = False
) -> None:
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


def pdf_to_image_entry_point(
    input_path: Path,
    output_directory: Path,
    /,
    pages_to_convert: Optional[str] = None,
    scale: int = 2,
    force: bool = False,
    verbose: bool = False
) -> None:
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


def extract_text_entry_point(
    input_path: Path,
    /,
    output_path: Optional[Path] = None,
    pages_to_extract_from: Optional[str] = None,
    max_number_of_characters: int = -1,
    characters_to_split: int = 0,
    reverse_lines: bool = False,
    force: bool = False,
    verbose: bool = False
) -> None:
    """Extract text from a PDF file.

    :param input_path: Path to PDF file to extract text from.
    :param output_path: Path to write extracted text to. (Writes to stdout if not
        provided)
    :param pages_to_extract_from: Pages to extract text from. Example: '1-5,7,9-11'
    :param max_number_of_characters: Maximum number of characters to extract in total.
    :param characters_to_split: Create a new file if the number of characters in the
        extracted text exceeds this value.
    :param reverse_lines: Reverse the characters in each line (Useful for Persian text)
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

    text = extract_text(
        input_path, pages_to_extract_from_, max_number_of_characters, reverse_lines
    )
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


def split_pdf_entry_point(
    input_path: Path,
    output_directory: Path,
    /,
    split_points: Optional[str] = None,
    force: bool = False,
    verbose: bool = False
) -> None:
    """Split a PDF file into multiple files.

    :param input_path: Path to PDF file to split.
    :param output_directory: Path to directory to write split files to.
    :param split_points: Comma-separated list of pages to split. Example: '5,7,9'
    :param force: Force overwrite of output directory.
    :param verbose: Print verbose output.
    """
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

    split_points_ = None
    if split_points:
        try:
            split_points_ = parse_pages(split_points)
        except ValueError:
            log21.critical(f'Invalid pages string: `{split_points}`')
            sys.exit(1)

    log21.info(f'Splitting `{input_path}`...')
    number_of_pdfs = split_pdf(input_path, output_directory, split_points_)
    if number_of_pdfs > 1:
        log21.info(f'Split {input_path} to {number_of_pdfs} PDF files!')


def watermark_pdf_entry_point(
    input_path: Path,
    output_path: Path,
    watermark_text: str,
    /,
    position: str = 'center',
    font_size: int = 36,
    opacity: float = 0.1,
    rotation: float = 45.0,
    force: bool = False,
    verbose: bool = False
) -> None:
    """Add a watermark to a PDF file.

    :param input_path: Path to PDF file to add watermark to.
    :param output_path: Path to write watermarked PDF file to.
    :param watermark_text: Text to use as watermark.
    :param position: Position of watermark. One of 'center' or '50% 50%', 'top-left' or
        '0% 0%', 'top-right' or '100% 0%', 'bottom-left' or '0% 100%', etc.
        You can also use absolute values like '100 100'.
        Note: The position is relative to the center of the watermark text.
    :param font_size: Font size of watermark text.
    :param opacity: Opacity of watermark text. Between 0.0 and 1.0.
    :param rotation: Rotation of watermark text in degrees.
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

    log21.info(f'Adding watermark to `{input_path}`...')
    try:
        number_of_pages = watermark_pdf(
            input_path, output_path, watermark_text, position, font_size, opacity,
            rotation
        )
        log21.info(
            f'Added watermark to {number_of_pages} page' +
            ('s' if number_of_pages > 1 else '') + '!'
        )
    except PermissionError:
        log21.critical(
            f'Cannot write to output file `{output_path}`.\n'
            'Check the file permissions and close any applications that may be using '
            'the file, then try again.'
        )
        sys.exit(1)
    except ValueError as e:
        log21.critical(str(e))
        sys.exit(1)


def main() -> None:
    try:
        if sys.platform == 'win32':
            import msvcrt
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        log21.basic_config(level=log21.ERROR)
        log21.argumentify(
            {
                'bundle': bundle_entry_point,
                'remove-pages': remove_pages_entry_point,
                'to-image': pdf_to_image_entry_point,
                'add-watermark': watermark_pdf_entry_point,
                'extract-text': extract_text_entry_point,
                'split': split_pdf_entry_point
            }
        )
    except KeyboardInterrupt:
        log21.critical('\nKeyboardInterrupt: Exiting...')
        sys.exit(1)


if __name__ == '__main__':
    main()
