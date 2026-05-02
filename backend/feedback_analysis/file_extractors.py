"""Convert uploaded PDF and plain-text files into a list of feedback comments.

Both extractors return ``list[str]`` and raise ``ValueError`` with a
user-friendly message when the file cannot be turned into comments. The
caller (``FeedbackFileIngestView``) translates that into an HTTP 400.

These are pure functions and intentionally have no Django dependency so they
can be unit-tested without bootstrapping the wider feedback-analysis stack.
"""

from __future__ import annotations

import zipfile
from typing import IO, List

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from pypdf import PdfReader
from pypdf.errors import FileNotDecryptedError, PdfReadError

_BOM = "﻿"


def _split_lines_to_comments(text: str) -> List[str]:
    """Normalize line endings, strip whitespace, and drop empty entries."""
    if not text:
        return []
    if text.startswith(_BOM):
        text = text[len(_BOM):]
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return [line.strip() for line in normalized.split("\n") if line.strip()]


def extract_comments_from_text(file_obj: IO[bytes]) -> List[str]:
    """Read a UTF-8 text upload and return one comment per non-empty line."""
    raw = file_obj.read()
    decoded = raw.decode("utf-8", errors="replace")
    comments = _split_lines_to_comments(decoded)
    if not comments:
        raise ValueError("Text file is empty.")
    return comments


def extract_comments_from_pdf(file_obj: IO[bytes]) -> List[str]:
    """Read a PDF upload and return one comment per non-empty extracted line."""
    try:
        reader = PdfReader(file_obj)
    except PdfReadError as exc:
        raise ValueError(f"PDF could not be read: {exc}") from exc

    if reader.is_encrypted:
        raise ValueError(
            "PDF is encrypted. Please remove the password before uploading."
        )

    comments: List[str] = []
    try:
        for page in reader.pages:
            page_text = page.extract_text() or ""
            comments.extend(_split_lines_to_comments(page_text))
    except FileNotDecryptedError as exc:
        raise ValueError(
            "PDF is encrypted. Please remove the password before uploading."
        ) from exc
    except PdfReadError as exc:
        raise ValueError(f"PDF could not be read: {exc}") from exc

    if not comments:
        raise ValueError(
            "PDF contains no extractable text. "
            "Encrypted or image-only (scanned) PDFs are not supported."
        )
    return comments


def extract_comments_from_docx(file_obj: IO[bytes]) -> List[str]:
    """Read a Word (.docx) upload and return one comment per non-empty paragraph.

    Also pulls text out of any tables, since users sometimes paste feedback
    into a single-column table.
    """
    try:
        doc = Document(file_obj)
    except (PackageNotFoundError, zipfile.BadZipFile) as exc:
        raise ValueError(
            "DOCX could not be read. The file may be corrupted or password-protected."
        ) from exc

    comments: List[str] = []
    for paragraph in doc.paragraphs:
        text = (paragraph.text or "").strip()
        if text:
            comments.append(text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                text = (cell.text or "").strip()
                if text:
                    comments.append(text)

    if not comments:
        raise ValueError(
            "DOCX contains no extractable text. The document appears to be empty."
        )
    return comments
