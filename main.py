#!/usr/bin/env python3
import io
import sys
from typing import Sequence, Collection
from pathlib import Path

import log21
from pypdf import PdfReader, PdfWriter


def merge_pdfs(
    input_files: Sequence[str | Path | io.TextIOWrapper],
    output_stream: io.BufferedWriter
):
    """Merge PDF files.

    :param input_files: List of PDF files to concatenate.
    :param output_stream: Output stream to write to.
    """
    writer = PdfWriter()
    for input_file in input_files:
        log21.info(f'Adding {input_file}...')
        reader = PdfReader(input_file)
        for i, page in enumerate(reader.pages):
            log21.info(f'Adding page {i + 1}...', end='\r')
            writer.add_page(page)  # type: ignore
    writer.write(output_stream)


def merge_pdfs_entry_point(
    output_path: Path,
    /,
    *input_paths: Path,
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
    input_file: str | Path | io.TextIOWrapper, pages_to_remove: Collection[int],
    output_stream: io.BufferedWriter
):
    """Remove pages from a PDF file.

    :param input_file: PDF file to remove pages from.
    :param pages_to_remove: List of pages to remove.
    :param output_stream: Output stream to write to.
    """
    writer = PdfWriter()
    reader = PdfReader(input_file)
    for i, page in enumerate(reader.pages):
        if i + 1 not in pages_to_remove:
            log21.info(f'Adding page {i + 1}...', end='\r')
            writer.add_page(page)  # type: ignore
    writer.write(output_stream)


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
    :param pages_to_remove: Comma-separated list of pages to remove. Example:
        '1-5,7,9-11'
    :param force: Force overwrite of output file.
    :param verbose: Print verbose output.
    """
    if not input_path.exists():
        log21.critical(f'Input file `{input_path}` does not exist.')
        sys.exit(1)
    if output_path.exists() and not force:
        log21.critical('Output file already exists.')
        sys.exit(1)
    if verbose:
        log21.basic_config(level=log21.INFO)

    try:
        pages_to_remove_ = parse_pages(pages_to_remove)
    except ValueError:
        log21.critical(f'Invalid pages string: `{pages_to_remove}`')
        sys.exit(1)

    log21.info(
        'Removing page' + (
            's ' + ', '.join(str(page) for page in pages_to_remove_[:-1]) +
            ' and' if len(pages_to_remove_) > 2 else ''
        ) + f' {pages_to_remove_[-1]} from `{input_path}`'
    )
    try:
        with open(output_path, 'wb') as output_file:
            remove_pages(input_path, pages_to_remove_, output_file)
    except PermissionError:
        log21.critical(
            f'Cannot write to output file `{output_path}`.\n'
            'Check the file permissions and close any applications that may be using '
            'the file, then try again.'
        )
        sys.exit(1)


if __name__ == '__main__':
    if sys.platform == 'win32':
        import os
        import msvcrt
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    log21.basic_config(level=log21.ERROR)
    log21.argumentify(
        {
            'merge': merge_pdfs_entry_point,
            'remove-pages': remove_pages_entry_point
        }
    )
