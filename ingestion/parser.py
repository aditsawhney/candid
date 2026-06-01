import hashlib
import pdfplumber
from pathlib import Path


def extract_text(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def hash_file(pdf_path: str) -> str:
    with open(pdf_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def parse_resume(pdf_path: str) -> dict:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"No file at {pdf_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF, got {path.suffix}")

    return {
        "raw_text": extract_text(pdf_path),
        "file_hash": hash_file(pdf_path),
        "filename": path.name,
    }