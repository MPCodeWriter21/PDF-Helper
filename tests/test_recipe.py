# yapf: disable

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml
import pytest
from pypdfium2 import PdfDocument

from tests.conftest import make_recipe
from pdf_helper.recipe import (OPERATIONS, Context, RecipeError, _load, run_recipe,
                               _handle_split, _handle_bundle, _handle_encrypt,
                               _handle_metadata, _handle_to_image, _handle_watermark,
                               _handle_extract_text, _handle_remove_pages)

# yapf: enable

# _load


def test_load_valid(tmp_path: Path) -> None:
    p = make_recipe({"steps": [{"id": "s", "operation": "remove_pages"}]}, tmp_path)
    assert _load(str(p)) == {"steps": [{"id": "s", "operation": "remove_pages"}]}


def test_load_missing_steps(tmp_path: Path) -> None:
    p = make_recipe({"name": "nope"}, tmp_path)
    with pytest.raises(RecipeError, match="steps"):
        _load(str(p))


def test_load_invalid_yaml(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text("{invalid: yaml: [broken")
    with pytest.raises(yaml.YAMLError):
        _load(str(p))


# Context.resolve


def test_resolve_plain_string() -> None:
    ctx = Context({"steps": []})
    assert ctx.resolve("hello.pdf") == "hello.pdf"


def test_resolve_temp_dir() -> None:
    ctx = Context({"steps": [], "settings": {"temp_dir": "/tmp/recipes"}})
    assert ctx.resolve("{temp_dir}/out.pdf") == "/tmp/recipes/out.pdf"


def test_resolve_temp_dir_default() -> None:
    ctx = Context({"steps": []})
    assert ctx.resolve("{temp_dir}/out.pdf") == "./.recipe-tmp/out.pdf"


def test_resolve_step_ref() -> None:
    ctx = Context({"steps": []})
    ctx.outputs["step1"] = "/tmp/bundled.pdf"
    assert ctx.resolve({"step": "step1"}) == "/tmp/bundled.pdf"


def test_resolve_step_ref_with_file() -> None:
    ctx = Context({"steps": []})
    ctx.outputs["split"] = "/tmp/pieces"
    expected = str(Path("/tmp/pieces") / "part2.pdf")
    assert ctx.resolve({"step": "split", "file": "part2.pdf"}) == expected


def test_resolve_step_unknown() -> None:
    ctx = Context({"steps": []})
    with pytest.raises(RecipeError, match="no tracked output"):
        ctx.resolve({"step": "nonexistent"})


def test_resolve_input_ref() -> None:
    ctx = Context({"steps": []})
    ctx.resolved_inputs["password"] = "secret123"
    assert ctx.resolve({"input": "password"}) == "secret123"


def test_resolve_input_unknown() -> None:
    ctx = Context({"steps": []})
    with pytest.raises(RecipeError, match="not defined"):
        ctx.resolve({"input": "missing"})


def test_resolve_path_with_pages() -> None:
    ctx = Context({"steps": []})
    result = ctx.resolve({"path": "doc.pdf", "pages": [1, 2]})
    assert isinstance(result, dict)
    assert result["path"] == "doc.pdf"
    assert result["pages"] == [1, 2]


# Context._resolve_inputs


def test_resolve_inputs_env_var() -> None:
    os.environ["TEST_PDF_PASS"] = "my_pass"
    ctx = Context({"steps": [], "inputs": {"password": {"env": "TEST_PDF_PASS"}}})
    assert ctx.resolved_inputs["password"] == "my_pass"
    del os.environ["TEST_PDF_PASS"]


def test_resolve_inputs_env_missing_with_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "typed_pass")
    ctx = Context(
        {
            "steps": [],
            "inputs": {
                "password": {
                    "env": "MISSING_VAR",
                    "prompt": "Enter pass:"
                }
            },
        }
    )
    assert ctx.resolved_inputs["password"] == "typed_pass"


def test_resolve_inputs_raw_value() -> None:
    ctx = Context({"steps": [], "inputs": {"name": "direct_value"}})
    assert ctx.resolved_inputs["name"] == "direct_value"


def test_resolve_inputs_complex_spec() -> None:
    ctx = Context({"steps": [], "inputs": {"opts": {"key": "val"}}})
    assert ctx.resolved_inputs["opts"] == {"key": "val"}


# Context.ensure_parent / cleanup


def test_ensure_parent_creates_dir(tmp_path: Path) -> None:
    nested = str(tmp_path / "a" / "b" / "out.pdf")
    ctx = Context({"steps": []})
    ctx.ensure_parent(nested)
    assert (tmp_path / "a" / "b").is_dir()


def test_cleanup_removes_temp_dir(tmp_path: Path) -> None:
    td = tmp_path / "recipe-tmp"
    td.mkdir()
    (td / "file.pdf").write_text("data")
    ctx = Context(
        {
            "steps": [],
            "settings": {
                "temp_dir": str(td),
                "cleanup_temp": True
            }
        }
    )
    ctx.cleanup()
    assert not td.exists()


def test_cleanup_noop_without_setting(tmp_path: Path) -> None:
    td = tmp_path / "no-clean"
    td.mkdir()
    ctx = Context({"steps": [], "settings": {"temp_dir": str(td)}})
    ctx.cleanup()
    assert td.exists()


# Handler: bundle (mocked core)


def test_handle_bundle_no_pages(tmp_path: Path) -> None:
    ctx = Context({"steps": [], "settings": {}})
    (tmp_path / "a.pdf").write_text("")
    step = {"inputs": [str(tmp_path / "a.pdf")], "output": str(tmp_path / "out.pdf")}
    with patch("pdf_helper.recipe._bundle") as mock:
        _handle_bundle(ctx, step)
    mock.assert_called_once()


def test_handle_bundle_with_pages(test_pdf: Path, tmp_path: Path) -> None:
    ctx = Context({"steps": [], "settings": {}})
    out = tmp_path / "out.pdf"
    step = {"inputs": [{"path": str(test_pdf), "pages": [1, 3, 5]}], "output": str(out)}
    result = _handle_bundle(ctx, step)
    assert result == str(out)
    assert out.exists()
    reader = PdfDocument(str(out))
    assert len(reader) == 3  # pages 1, 3, 5
    reader.close()


def test_handle_bundle_mixed(test_pdf: Path, tmp_path: Path) -> None:
    ctx = Context({"steps": [], "settings": {}})
    out = tmp_path / "out.pdf"
    step = {
        "inputs": [str(test_pdf), {
            "path": str(test_pdf),
            "pages": [1, 2]
        }],
        "output": str(out),
    }
    result = _handle_bundle(ctx, step)
    assert result == str(out)
    assert out.exists()
    reader = PdfDocument(str(out))
    assert len(reader) == 7  # 5 full + 2 selected
    reader.close()


def test_handle_bundle_invalid_input(test_pdf: Path) -> None:
    ctx = Context({"steps": [], "settings": {}})
    step = {
        "inputs": [{
            "path": str(test_pdf),
            "pages": [1]
        }, 42],
        "output": str(test_pdf.parent / "out.pdf"),
    }
    with pytest.raises(RecipeError, match="Invalid bundle"):
        _handle_bundle(ctx, step)


# Handler: remove_pages (mocked core)


def test_handle_remove_pages_delegates() -> None:
    ctx = Context({"steps": []})
    step = {"input": "in.pdf", "pages_to_remove": [2, 4], "output": "out.pdf"}
    with patch("pdf_helper.recipe._remove_pages") as mock:
        result = _handle_remove_pages(ctx, step)
    mock.assert_called_once_with("in.pdf", [2, 4], "out.pdf")
    assert result == "out.pdf"


# Handler: split (mocked core)


def test_handle_split_no_prefix(test_pdf: Path, tmp_path: Path) -> None:
    ctx = Context({"steps": [], "settings": {}})
    step = {
        "input": str(test_pdf),
        "split_points": [3],
        "output_dir": str(tmp_path / "parts"),
        "output": str(tmp_path / "parts"),
    }
    _handle_split(ctx, step)
    assert (tmp_path / "parts").is_dir()


# Handler: to_image (mocked core)


def test_handle_to_image(tmp_path: Path) -> None:
    ctx = Context({"steps": []})
    (tmp_path / "in.pdf").write_text("")
    step = {
        "input": str(tmp_path / "in.pdf"),
        "pages": "1-3",
        "scale": 3,
        "output": str(tmp_path / "imgs"),
    }
    with patch("pdf_helper.recipe._pdf_to_image") as mock:
        _handle_to_image(ctx, step)
    mock.assert_called_once_with(
        str(tmp_path / "in.pdf"), str(tmp_path / "imgs"), [1, 2, 3], 3
    )


# Handler: extract_text (mocked core)


def test_handle_extract_text(tmp_path: Path) -> None:
    ctx = Context({"steps": []})
    (tmp_path / "in.pdf").write_text("")
    step = {
        "input": str(tmp_path / "in.pdf"),
        "pages": "1-2",
        "max_characters": 100,
        "reverse_lines": True,
        "output": str(tmp_path / "out.txt"),
    }
    with patch("pdf_helper.recipe._extract_text", return_value="hello") as mock:
        _handle_extract_text(ctx, step)
    mock.assert_called_once_with(str(tmp_path / "in.pdf"), [1, 2], 100, True)
    assert (tmp_path / "out.txt").read_text() == "hello"


# Handlers: NotImplementedError fallback


@patch("pdf_helper.recipe._watermark_pdf", side_effect=NotImplementedError)
def test_handle_watermark_fallback(mock_func: MagicMock, tmp_path: Path) -> None:
    src = tmp_path / "in.pdf"
    src.write_text("pdf data")
    ctx = Context({"steps": []})
    step = {"input": str(src), "text": "DRAFT", "output": str(tmp_path / "out.pdf")}
    result = _handle_watermark(ctx, step)
    assert result == str(tmp_path / "out.pdf")
    assert (tmp_path / "out.pdf").read_text() == "pdf data"


@patch("pdf_helper.recipe._encrypt_pdf", side_effect=NotImplementedError)
def test_handle_encrypt_fallback(mock_func: MagicMock, tmp_path: Path) -> None:
    src = tmp_path / "in.pdf"
    src.write_text("pdf data")
    ctx = Context({"steps": []})
    step = {
        "input": str(src),
        "password": "secret",
        "output": str(tmp_path / "out.pdf"),
    }
    result = _handle_encrypt(ctx, step)
    assert result == str(tmp_path / "out.pdf")
    assert (tmp_path / "out.pdf").read_text() == "pdf data"


@patch("pdf_helper.recipe._set_metadata", side_effect=NotImplementedError)
def test_handle_metadata_fallback(mock_func: MagicMock, tmp_path: Path) -> None:
    src = tmp_path / "in.pdf"
    src.write_text("pdf data")
    ctx = Context({"steps": []})
    step = {
        "input": str(src),
        "title": "Test",
        "author": "Me",
        "output": str(tmp_path / "out.pdf"),
    }
    result = _handle_metadata(ctx, step)
    assert result == str(tmp_path / "out.pdf")
    assert (tmp_path / "out.pdf").read_text() == "pdf data"


# OPERATIONS registry


def test_all_operations_registered() -> None:
    expected = {
        "bundle",
        "remove_pages",
        "split_pdf",
        "pdf_to_image",
        "extract_text",
        "watermark",
        "encrypt",
        "metadata",
    }
    assert set(OPERATIONS.keys()) == expected


# run_recipe: success


def test_run_recipe_success(test_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "cleaned.pdf"
    recipe = {
        "name":
        "test",
        "steps": [
            {
                "id": "clean",
                "operation": "remove_pages",
                "input": str(test_pdf),
                "pages_to_remove": [1],
                "output": str(out),
            }
        ],
    }
    p = make_recipe(recipe, tmp_path)
    run_recipe(str(p))
    assert out.exists()


def test_run_recipe_multiple_steps(test_pdf: Path, tmp_path: Path) -> None:
    mid = tmp_path / "mid.pdf"
    final = tmp_path / "final.pdf"
    recipe = {
        "name":
        "chain",
        "steps": [
            {
                "id": "a",
                "operation": "remove_pages",
                "input": str(test_pdf),
                "pages_to_remove": [1, 2],
                "output": str(mid),
            },
            {
                "id": "b",
                "operation": "remove_pages",
                "input": {
                    "step": "a"
                },
                "pages_to_remove": [1],
                "output": str(final),
            },
        ],
    }
    p = make_recipe(recipe, tmp_path)
    run_recipe(str(p))
    assert mid.exists()
    assert final.exists()
    reader = PdfDocument(str(final))
    assert len(reader) == 2  # 5 - 2 - 1 = 2
    reader.close()


# run_recipe: error handling


def test_run_recipe_overwrite_protection(test_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.pdf"
    out.write_text("existing")
    recipe = {
        "steps": [
            {
                "operation": "remove_pages",
                "input": str(test_pdf),
                "pages_to_remove": [],
                "output": str(out),
            }
        ]
    }
    p = make_recipe(recipe, tmp_path)
    with pytest.raises(SystemExit):
        run_recipe(str(p))


def test_run_recipe_force_override(test_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.pdf"
    out.write_text("existing")
    recipe = {
        "steps": [
            {
                "operation": "remove_pages",
                "input": str(test_pdf),
                "pages_to_remove": [],
                "output": str(out),
            }
        ]
    }
    os.environ["PDF_HELPER_RECIPE_FORCE"] = "1"
    p = make_recipe(recipe, tmp_path)
    run_recipe(str(p))
    assert out.exists()
    os.environ.pop("PDF_HELPER_RECIPE_FORCE", None)


def test_run_recipe_unknown_operation(tmp_path: Path) -> None:
    recipe = {
        "steps": [
            {
                "id": "x",
                "operation": "nonexistent",
                "input": "in.pdf",
                "output": "out.pdf",
            }
        ]
    }
    p = make_recipe(recipe, tmp_path)
    with pytest.raises(SystemExit):
        run_recipe(str(p))


def test_run_recipe_cleanup_on_success(test_pdf: Path, tmp_path: Path) -> None:
    td = tmp_path / "recipe-tmp"
    recipe = {
        "settings": {
            "temp_dir": str(td),
            "cleanup_temp": True
        },
        "steps": [
            {
                "operation": "remove_pages",
                "input": str(test_pdf),
                "pages_to_remove": [],
                "output": str(td / "out.pdf"),
            }
        ],
    }
    p = make_recipe(recipe, tmp_path)
    run_recipe(str(p))
    assert not td.exists()


def test_run_recipe_cleanup_on_failure(tmp_path: Path) -> None:
    td = tmp_path / "recipe-tmp"
    td.mkdir()
    recipe = {
        "settings": {
            "temp_dir": str(td),
            "cleanup_temp": True
        },
        "steps": [{
            "operation": "nonexistent",
            "output": str(td / "out.pdf")
        }],
    }
    p = make_recipe(recipe, tmp_path)
    with pytest.raises(SystemExit):
        run_recipe(str(p))
    assert not td.exists()


# Integration: run example recipe files


def test_example_recipes_parse() -> None:
    base = Path(__file__).resolve().parent.parent / "examples" / "recipes"
    for recipe_file in sorted(base.glob("*.yaml")):
        data = _load(str(recipe_file))
        assert "steps" in data
        assert len(data["steps"]) > 0
        for step in data["steps"]:
            assert "operation" in step
            assert step["operation"] in OPERATIONS


def test_example_remove_pages(test_pdf: Path, tmp_path: Path) -> None:
    base = Path(__file__).resolve().parent.parent / "examples" / "recipes"
    recipe_path = base / "remove-pages.yaml"
    os.chdir(str(tmp_path))
    (tmp_path / "document.pdf").write_bytes(test_pdf.read_bytes())
    run_recipe(str(recipe_path))
    assert (tmp_path / "cleaned.pdf").exists()
    reader = PdfDocument(str(tmp_path / "cleaned.pdf"))
    assert len(reader) == 3  # 5 pages - [2,4] = 3 (page 6 is out of range, ignored)
    reader.close()


def test_example_bundle_with_pages(test_pdf: Path, tmp_path: Path) -> None:
    base = Path(__file__).resolve().parent.parent / "examples" / "recipes"
    recipe_path = base / "bundle-with-pages.yaml"
    os.chdir(str(tmp_path))
    (tmp_path / "cover.pdf").write_bytes(test_pdf.read_bytes())
    (tmp_path / "chapter-1.pdf").write_bytes(test_pdf.read_bytes())
    (tmp_path / "logo.png").write_text("fake png")  # will fail but tests parsing
    (tmp_path / "chapter-2.pdf").write_bytes(test_pdf.read_bytes())
    (tmp_path / "appendix.pdf").write_bytes(test_pdf.read_bytes())
    from pdf_helper.recipe import Context, _load

    data = _load(str(recipe_path))
    ctx = Context(data)
    steps = data["steps"]
    # Just verify the first step parses and resolves correctly
    resolved = ctx.resolve(steps[0]["inputs"][0])
    assert resolved == "cover.pdf"  # resolve returns the string as-is (no cwd joining)
