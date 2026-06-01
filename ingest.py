import sys
from ingestion.parser import parse_resume
from ingestion.extractor import extract_resume
from ingestion.loader import load_resume

if __name__ == "__main__":
    pdf_path = sys.argv[1]
    print(f"Parsing {pdf_path}...")
    parsed = parse_resume(pdf_path)
    print("Extracting...")
    extracted = extract_resume(parsed["raw_text"])
    print(f"Extracted: {extracted}")
    candidate = load_resume(parsed, extracted)
    print(f"Done. Candidate: {extracted.get('name')}")