"""
Extracts plain text (plus page-level structure where available) from an
uploaded document. Each extractor returns a list of (page_number, text)
tuples so downstream chunking can preserve page traceability. Non-paginated
formats (txt/md/json/yaml/csv) use page=None.
"""
import csv
import io
import json
import yaml
from app.utils.text_cleaning import clean_text


class ExtractionError(Exception):
    pass


SUPPORTED_TYPES = {"pdf", "docx", "txt", "md", "csv", "json", "yaml", "yml"}


def guess_file_type(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "yml":
        ext = "yaml"
    return ext


def extract_text(filename: str, data: bytes):
    """Returns (file_type, list[(page_or_none, text)])."""
    file_type = guess_file_type(filename)
    if file_type not in SUPPORTED_TYPES:
        raise ExtractionError(f"Unsupported file type: .{file_type}")

    try:
        if file_type == "pdf":
            return file_type, _extract_pdf(data)
        elif file_type == "docx":
            return file_type, _extract_docx(data)
        elif file_type in ("txt", "md"):
            return file_type, _extract_plain(data)
        elif file_type == "csv":
            return file_type, _extract_csv(data)
        elif file_type == "json":
            return file_type, _extract_json(data)
        elif file_type in ("yaml", "yml"):
            return file_type, _extract_yaml(data)
    except ExtractionError:
        raise
    except Exception as e:
        raise ExtractionError(f"Failed to parse {file_type} file: {e}")


def _extract_pdf(data: bytes):
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise ExtractionError(f"PyMuPDF not available: {e}")

    pages = []
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as e:
        raise ExtractionError(f"Corrupted or unreadable PDF: {e}")

    total_chars = 0
    for i, page in enumerate(doc):
        text = page.get_text("text") or ""
        total_chars += len(text.strip())
        pages.append((i + 1, clean_text(text)))
    doc.close()

    if total_chars < 20:
        raise ExtractionError(
            "PDF appears to contain no extractable text (likely a scanned "
            "image). OCR is not currently enabled for this document."
        )
    return pages


def _extract_docx(data: bytes):
    try:
        import docx
    except ImportError as e:
        raise ExtractionError(f"python-docx not available: {e}")

    try:
        d = docx.Document(io.BytesIO(data))
    except Exception as e:
        raise ExtractionError(f"Corrupted or unreadable DOCX: {e}")

    full_text = "\n\n".join(p.text for p in d.paragraphs if p.text.strip())
    if not full_text.strip():
        raise ExtractionError("DOCX file contains no readable text.")
    return [(None, clean_text(full_text))]


def _extract_plain(data: bytes):
    try:
        text = data.decode("utf-8", errors="replace")
    except Exception as e:
        raise ExtractionError(f"Could not decode text file: {e}")
    if not text.strip():
        raise ExtractionError("File is empty.")
    return [(None, clean_text(text))]


def _extract_csv(data: bytes):
    try:
        text = data.decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
    except Exception as e:
        raise ExtractionError(f"Could not parse CSV: {e}")
    if not rows:
        raise ExtractionError("CSV file is empty.")
    header = rows[0]
    lines = []
    for row in rows[1:]:
        pairs = [f"{h}: {v}" for h, v in zip(header, row)]
        lines.append(" | ".join(pairs))
    return [(None, clean_text("\n".join(lines)))]


def _extract_json(data: bytes):
    try:
        obj = json.loads(data.decode("utf-8", errors="replace"))
    except Exception as e:
        raise ExtractionError(f"Invalid JSON: {e}")
    return [(None, clean_text(json.dumps(obj, indent=2)))]


def _extract_yaml(data: bytes):
    try:
        obj = yaml.safe_load(data.decode("utf-8", errors="replace"))
    except Exception as e:
        raise ExtractionError(f"Invalid YAML: {e}")
    return [(None, clean_text(yaml.dump(obj)))]
