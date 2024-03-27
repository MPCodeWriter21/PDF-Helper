#!/usr/bin/env python3
import io
import sys
from typing import Sequence
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
    try:
        writer = PdfWriter()
        for input_file in input_files:
            log21.info(f'Adding {input_file}...')
            reader = PdfReader(input_file)
            for i, page in enumerate(reader.pages):
                log21.info(f'Adding page {i + 1}...', end='\r')
                writer.add_page(page)  # type: ignore
        writer.write(output_stream)
    finally:
        output_stream.close()


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
    with open(output_path, 'wb') as output_file:
        merge_pdfs(input_paths, output_file)


if __name__ == '__main__':
    if sys.platform == 'win32':
        import os
        import msvcrt
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    log21.basic_config(level=log21.ERROR)
    log21.argumentify({'merge': merge_pdfs_entry_point})
