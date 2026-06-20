# yapf: disable

import os
import sys
import shutil
from pathlib import Path

import yaml
import log21
import pypdfium2 as pdfium
from pypdfium2 import PdfImage, PdfBitmap, PdfDocument

from . import (bundle as _bundle, split_pdf as _split_pdf, encrypt_pdf as _encrypt_pdf,
               extract_text as _extract_text, pdf_to_image as _pdf_to_image,
               remove_pages as _remove_pages, set_metadata as _set_metadata,
               watermark_pdf as _watermark_pdf)
from .utils import parse_pages

# yapf: enable


class RecipeError(Exception):
    pass


def _load(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        recipe = yaml.safe_load(f)
    if not isinstance(recipe, dict) or "steps" not in recipe:
        raise RecipeError("Recipe must contain a 'steps' list")
    return recipe


class Context:

    def __init__(self, recipe: dict) -> None:
        self.recipe = recipe
        self.settings = recipe.get("settings", {})
        self.outputs: dict[str, str] = {}
        self.resolved_inputs: dict[str, object] = {}
        self._resolve_inputs()

    def _resolve_inputs(self) -> None:
        for name, spec in self.recipe.get("inputs", {}).items():
            if isinstance(spec, dict):
                if "env" in spec:
                    value = os.environ.get(spec["env"])
                    if not value and "prompt" in spec:
                        value = input(f"{spec['prompt']}: ")
                    self.resolved_inputs[name] = value or ""
                else:
                    self.resolved_inputs[name] = spec
            else:
                self.resolved_inputs[name] = spec

    def resolve(self, value: object) -> object:
        if isinstance(value, str):
            if "{temp_dir}" in value:
                td = self.settings.get("temp_dir", "./.recipe-tmp")
                value = value.replace("{temp_dir}", td)
            return value
        if isinstance(value, dict):
            if "step" in value:
                base = self.outputs.get(value["step"])
                if base is None:
                    raise RecipeError(f"Step '{value['step']}' has no tracked output")
                if "file" in value:
                    return str(Path(base) / value["file"])
                return base
            if "input" in value:
                name = value["input"]
                if name not in self.resolved_inputs:
                    raise RecipeError(f"Input '{name}' is not defined")
                return self.resolved_inputs[name]
            if "path" in value:
                value["path"] = self.resolve(value["path"])
            return value
        return value

    def ensure_parent(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    def cleanup(self) -> None:
        if self.settings.get("cleanup_temp"):
            td = self.settings.get("temp_dir")
            if td and os.path.isdir(td):
                shutil.rmtree(td, ignore_errors=True)


# ── Handlers ────────────────────────────────────────────────────────


def _handle_bundle(ctx: Context, step: dict) -> str:
    inputs = step.get("inputs", [])
    output = ctx.resolve(step["output"])
    ctx.ensure_parent(output)

    has_page_selection = any(isinstance(s, dict) and "pages" in s for s in inputs)

    if not has_page_selection:
        resolved = [ctx.resolve(s) for s in inputs]
        log21.info(f"Bundling {len(resolved)} files...")
        _bundle(resolved, output)
        return output

    writer = PdfDocument.new()
    for spec in inputs:
        if isinstance(spec, str):
            path = ctx.resolve(spec)
            log21.info(f"Adding '{path}' (all pages)...")
            _import_into_writer(writer, path)
        elif isinstance(spec, dict):
            path = ctx.resolve(spec["path"])
            pages_spec = spec.get("pages")
            if pages_spec and str(path).lower().endswith(".pdf"):
                if isinstance(pages_spec, str):
                    pages = parse_pages(pages_spec)
                else:
                    pages = list(pages_spec)
                pages_zero = [p - 1 for p in pages]
                log21.info(f"Adding '{path}' pages {pages}...")
                reader = PdfDocument(path)
                writer.import_pages(reader, pages_zero)
                reader.close()
            else:
                log21.info(f"Adding '{path}'...")
                _import_into_writer(writer, path)
        else:
            raise RecipeError(f"Invalid bundle input: {spec}")

    writer.save(output)
    count = len(writer)
    writer.close()
    log21.info(f"Bundled {count} pages to {output}")
    return output


def _import_into_writer(writer: PdfDocument, path: str) -> None:
    if str(path).lower().endswith(".pdf"):
        reader = PdfDocument(path)
        writer.import_pages(reader)
        reader.close()
    else:
        from PIL import Image

        image = Image.open(path)
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


def _handle_remove_pages(ctx: Context, step: dict) -> str:
    input_file = ctx.resolve(step["input"])
    pages = step.get("pages_to_remove", [])
    output = ctx.resolve(step["output"])
    ctx.ensure_parent(output)
    log21.info(f"Removing pages {pages} from '{input_file}'...")
    _remove_pages(input_file, pages, output)
    return output


def _handle_split(ctx: Context, step: dict) -> str:
    input_file = ctx.resolve(step["input"])
    output_dir = ctx.resolve(step.get("output_dir", "."))
    prefix = step.get("output_prefix", "")
    split_points = step.get("split_points")

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    log21.info(f"Splitting '{input_file}'...")
    _split_pdf(input_file, output_dir, split_points)

    if prefix:
        out = Path(output_dir)
        stem = Path(input_file).stem
        for f in sorted(out.glob(f"{stem}_part_*.pdf")):
            new = out / f.name.replace(f"{stem}_part_", prefix)
            f.rename(new)

    return str(output_dir)


def _handle_to_image(ctx: Context, step: dict) -> str:
    input_file = ctx.resolve(step["input"])
    output = ctx.resolve(step["output"])
    pages = step.get("pages")
    scale = step.get("scale", 2)

    pages_parsed = parse_pages(pages) if isinstance(pages, str) else pages

    Path(output).mkdir(parents=True, exist_ok=True)
    log21.info(f"Converting '{input_file}' to images...")
    _pdf_to_image(input_file, output, pages_parsed, scale)
    return str(output)


def _handle_extract_text(ctx: Context, step: dict) -> str:
    input_file = ctx.resolve(step["input"])
    output = ctx.resolve(step["output"])
    pages = step.get("pages")
    max_chars = step.get("max_characters", -1)
    reverse = step.get("reverse_lines", False)

    pages_parsed = parse_pages(pages) if isinstance(pages, str) else pages

    ctx.ensure_parent(output)
    log21.info(f"Extracting text from '{input_file}'...")
    text = _extract_text(input_file, pages_parsed, max_chars, reverse)
    with open(output, "w", encoding="utf-8") as f:
        f.write(text)
    return str(output)


def _handle_watermark(ctx: Context, step: dict) -> str:
    input_file = ctx.resolve(step["input"])
    output = ctx.resolve(step["output"])
    text = step.get("text", "")
    position = step.get("position", "center")
    opacity = step.get("opacity", 0.1)
    rotation = step.get("rotation", 45.0)
    font_size = step.get("font_size", 36)

    ctx.ensure_parent(output)
    log21.info(f"Adding watermark to '{input_file}'...")
    try:
        _watermark_pdf(input_file, output, text, position, font_size, opacity, rotation)
    except NotImplementedError:
        log21.warning("Watermark is not yet implemented; copying input as-is.")
        shutil.copy2(input_file, output)
    return str(output)


def _handle_encrypt(ctx: Context, step: dict) -> str:
    input_file = ctx.resolve(step["input"])
    output = ctx.resolve(step["output"])
    password = ctx.resolve(step.get("password", ""))
    algorithm = step.get("algorithm", "AES-256")

    ctx.ensure_parent(output)
    log21.info(f"Encrypting '{input_file}'...")
    try:
        _encrypt_pdf(input_file, output, password, algorithm)
    except NotImplementedError:
        log21.warning("Encryption is not yet implemented; copying input as-is.")
        shutil.copy2(input_file, output)
    return str(output)


def _handle_metadata(ctx: Context, step: dict) -> str:
    input_file = ctx.resolve(step["input"])
    output = ctx.resolve(step["output"])
    meta = {
        k: step[k]
        for k in ("title", "author", "subject", "keywords", "producer") if k in step
    }

    ctx.ensure_parent(output)
    log21.info(f"Setting metadata on '{input_file}'...")
    try:
        _set_metadata(input_file, output, meta)
    except NotImplementedError:
        log21.warning(
            "Metadata operations are not yet implemented; copying input as-is."
        )
        shutil.copy2(input_file, output)
    return str(output)


# ── Registry ────────────────────────────────────────────────────────

OPERATIONS = {
    "bundle": _handle_bundle,
    "remove_pages": _handle_remove_pages,
    "split_pdf": _handle_split,
    "pdf_to_image": _handle_to_image,
    "extract_text": _handle_extract_text,
    "watermark": _handle_watermark,
    "encrypt": _handle_encrypt,
    "metadata": _handle_metadata,
}


def run_recipe(recipe_path: str | Path) -> None:
    recipe = _load(recipe_path)
    ctx = Context(recipe)

    name = recipe.get("name", Path(recipe_path).stem)
    log21.info(f"Running recipe: {name}")

    overwrite = ctx.settings.get("overwrite", False)
    if os.environ.pop("PDF_HELPER_RECIPE_FORCE", None) == "1":
        overwrite = True

    try:
        for step in recipe["steps"]:
            step_id = step.get("id", "")
            op = step.get("operation", "")
            handler = OPERATIONS.get(op)
            if handler is None:
                raise RecipeError(f"Step '{step_id}': unknown operation '{op}'")

            output_path = step.get("output")
            if output_path:
                resolved = ctx.resolve(output_path)
                if os.path.exists(resolved) and not overwrite:
                    raise RecipeError(
                        f"Output '{resolved}' already exists "
                        f"(set overwrite: true or remove the file)"
                    )

            log21.info(f"[{step_id}] {op}...")
            result = handler(ctx, step)
            ctx.outputs[step_id] = result
            log21.info(f"[{step_id}] Done -> {result}")

        log21.info(f"Recipe '{name}' completed successfully!")
    except RecipeError:
        log21.critical(f"Recipe failed: {sys.exc_info()[1]}")
        sys.exit(1)
    except Exception:
        log21.critical(f"Unexpected error in recipe: {sys.exc_info()[1]}")
        sys.exit(1)
    finally:
        ctx.cleanup()
