"""
Core redaction engine.

Detects U.S. Social Security Numbers in PDF and JPG files and produces
redacted copies. All processing is local — nothing is sent externally.

Supports SSN formats:
    123-45-6789
    123 45 6789
    123456789
"""

from __future__ import annotations

import logging
import os
import re
import shutil
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SSN_PATTERN = re.compile(r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b")
REDACTION_TEXT = "XXX-XX-XXXX"
SUPPORTED_PDF_EXTS = frozenset({".pdf"})
SUPPORTED_IMAGE_EXTS = frozenset({".jpg", ".jpeg"})
SUPPORTED_EXTS = SUPPORTED_PDF_EXTS | SUPPORTED_IMAGE_EXTS

MAX_FILE_SIZE_MB = 500


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

class Status(Enum):
    OK = auto()
    NO_TEXT = auto()
    CLEAN = auto()
    ERROR = auto()


@dataclass
class FileResult:
    filename: str
    status: Status
    ssn_count: int = 0
    error: str = ""


@dataclass
class BatchResult:
    results: list[FileResult] = field(default_factory=list)
    output_folder: str = ""

    @property
    def total_redacted(self) -> int:
        return sum(r.ssn_count for r in self.results)

    @property
    def total_errors(self) -> int:
        return sum(1 for r in self.results if r.status == Status.ERROR)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_folder(path: str) -> Path:
    """Validate and resolve a folder path. Raises ValueError on problems."""
    folder = Path(path).resolve()
    if not folder.exists():
        raise ValueError(f"Path does not exist: {folder}")
    if not folder.is_dir():
        raise ValueError(f"Path is not a directory: {folder}")
    return folder


def _validate_file(path: Path) -> None:
    """Raise ValueError if a file is too large or not a regular file."""
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(
            f"File exceeds {MAX_FILE_SIZE_MB} MB limit: {path.name} ({size_mb:.1f} MB)"
        )


def collect_files(folder: Path) -> list[str]:
    """Return sorted list of supported filenames in a folder."""
    return sorted(
        f.name for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS
    )


# ---------------------------------------------------------------------------
# SSN detection
# ---------------------------------------------------------------------------

def find_ssns(text: str) -> list[re.Match]:
    """Return all regex matches for SSN patterns in text."""
    return list(SSN_PATTERN.finditer(text))


# ---------------------------------------------------------------------------
# PDF redaction
# ---------------------------------------------------------------------------

def _redact_pdf_page(page: fitz.Page, matches: list[re.Match]) -> int:
    """Apply redaction annotations for each SSN match on a PDF page."""
    count = 0
    for match in matches:
        for rect in page.search_for(match.group()):
            page.add_redact_annot(
                rect, text=REDACTION_TEXT, fontsize=10, fill=(1, 1, 1)
            )
            count += 1
    if count > 0:
        page.apply_redactions()
    return count


def process_pdf(input_path: Path, output_path: Path) -> FileResult:
    """Detect SSNs with pdfplumber, redact with PyMuPDF."""
    _validate_file(input_path)
    result = FileResult(filename=input_path.name, status=Status.CLEAN)

    # Extract text per page and locate SSNs
    ssn_matches_by_page: dict[int, list[re.Match]] = {}
    has_text = False

    with pdfplumber.open(str(input_path)) as pdf:
        for idx, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if text.strip():
                has_text = True
            matches = find_ssns(text)
            if matches:
                ssn_matches_by_page[idx] = matches

    if not has_text:
        result.status = Status.NO_TEXT
        return result

    if not ssn_matches_by_page:
        # Clean file — copy as-is so output folder is complete
        shutil.copy2(input_path, output_path)
        return result

    # Apply redactions
    doc = fitz.open(str(input_path))
    try:
        for idx, matches in ssn_matches_by_page.items():
            result.ssn_count += _redact_pdf_page(doc[idx], matches)
        doc.save(str(output_path))
    finally:
        doc.close()

    result.status = Status.OK
    return result


# ---------------------------------------------------------------------------
# Image redaction (requires Tesseract OCR)
# ---------------------------------------------------------------------------

def _find_word_boxes(
    ssn_text: str,
    words: list[tuple[str, tuple[int, int, int, int]]],
) -> list[tuple[int, int, int, int]]:
    """
    Locate the bounding boxes of OCR words that compose an SSN string.

    Handles single-word matches (e.g. "123-45-6789") and multi-word
    matches where OCR splits the SSN (e.g. "123", "-", "45", "-", "6789").
    """
    digits = re.sub(r"[- ]", "", ssn_text)

    # Single-word match
    for word_text, box in words:
        if digits in re.sub(r"[- ]", "", word_text):
            return [box]

    # Multi-word sliding window (max 7 tokens covers all SSN splits)
    for start in range(len(words)):
        combined = ""
        boxes: list[tuple[int, int, int, int]] = []
        for end in range(start, min(start + 7, len(words))):
            combined += re.sub(r"[- ]", "", words[end][0])
            boxes.append(words[end][1])
            if digits in combined:
                return boxes
            if len(combined) > len(digits) + 5:
                break
    return []


def process_image(input_path: Path, output_path: Path) -> FileResult:
    """OCR with Tesseract, then redact SSNs by drawing over them."""
    import pytesseract
    from PIL import Image, ImageDraw

    _validate_file(input_path)
    result = FileResult(filename=input_path.name, status=Status.CLEAN)

    img = Image.open(input_path).convert("RGB")
    ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    full_text = " ".join(ocr_data["text"])
    if not full_text.strip():
        result.status = Status.NO_TEXT
        return result

    matches = find_ssns(full_text)
    if not matches:
        shutil.copy2(input_path, output_path)
        return result

    # Build word bounding-box index
    words = []
    for i in range(len(ocr_data["text"])):
        word = ocr_data["text"][i].strip()
        if word:
            x, y = ocr_data["left"][i], ocr_data["top"][i]
            w, h = ocr_data["width"][i], ocr_data["height"][i]
            words.append((word, (x, y, x + w, y + h)))

    draw = ImageDraw.Draw(img)
    for match in matches:
        boxes = _find_word_boxes(match.group(), words)
        if not boxes:
            continue
        x0 = min(b[0] for b in boxes)
        y0 = min(b[1] for b in boxes)
        x1 = max(b[2] for b in boxes)
        y1 = max(b[3] for b in boxes)
        draw.rectangle([x0, y0, x1, y1], fill="white")
        draw.text((x0, y0), REDACTION_TEXT, fill="black")
        result.ssn_count += 1

    img.save(output_path, quality=95)
    result.status = Status.OK
    return result


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------

def process_file(input_path: Path, output_path: Path) -> FileResult:
    """Route a single file to the correct processor."""
    ext = input_path.suffix.lower()
    if ext in SUPPORTED_PDF_EXTS:
        return process_pdf(input_path, output_path)
    if ext in SUPPORTED_IMAGE_EXTS:
        return process_image(input_path, output_path)
    return FileResult(
        filename=input_path.name, status=Status.ERROR,
        error=f"Unsupported extension: {ext}",
    )


def process_folder(
    input_folder: str,
    output_dir_name: str = "redacted_pdfs",
    on_progress: callable = None,
) -> BatchResult:
    """
    Process all supported files in a folder.

    Args:
        input_folder: Path to the folder containing files.
        output_dir_name: Name of the output subdirectory.
        on_progress: Optional callback(filename, index, total) for UI updates.

    Returns:
        BatchResult with per-file results and the output folder path.
    """
    folder = validate_folder(input_folder)
    filenames = collect_files(folder)
    batch = BatchResult()

    if not filenames:
        return batch

    output_folder = folder / output_dir_name
    output_folder.mkdir(exist_ok=True)
    batch.output_folder = str(output_folder)

    for idx, name in enumerate(filenames):
        if on_progress:
            on_progress(name, idx, len(filenames))

        input_path = folder / name
        output_path = output_folder / name

        try:
            result = process_file(input_path, output_path)
        except Exception as exc:
            log.exception("Failed to process %s", name)
            result = FileResult(
                filename=name, status=Status.ERROR, error=str(exc)
            )

        batch.results.append(result)

    return batch
