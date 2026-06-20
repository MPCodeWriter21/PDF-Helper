import os
import tempfile
from pathlib import Path

import yaml
import pytest
from pypdfium2 import PdfDocument


@pytest.fixture
def tmp_root() -> Path:
    with tempfile.TemporaryDirectory(prefix="pdf_helper_test_") as d:
        old = os.getcwd()
        os.chdir(d)
        yield Path(d)
        os.chdir(old)


@pytest.fixture
def test_pdf(tmp_root: Path) -> Path:
    path = tmp_root / "input.pdf"
    writer = PdfDocument.new()
    for _ in range(5):
        writer.new_page(612, 792)
    writer.save(str(path))
    writer.close()
    return path


@pytest.fixture
def test_pdf_pages(test_pdf: Path) -> int:
    reader = PdfDocument(str(test_pdf))
    n = len(reader)
    reader.close()
    return n


def make_recipe(data: dict, root: Path, name: str = "recipe.yaml") -> Path:
    path = root / name
    with open(str(path), "w") as f:
        yaml.dump(data, f)
    return path
