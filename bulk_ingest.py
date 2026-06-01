import os
import sys
import time
import httpx
from pathlib import Path

API_URL = "https://candid-nx0c.onrender.com"

def ingest_folder(folder: str):
    pdfs = sorted(Path(folder).glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {folder}")
        sys.exit(1)

    print(f"Found {len(pdfs)} PDFs — uploading to {API_URL}\n")
    success, failed = [], []

    for pdf in pdfs:
        try:
            with open(pdf, "rb") as f:
                r = httpx.post(
                    f"{API_URL}/candidates",
                    files={"file": (pdf.name, f, "application/pdf")},
                    timeout=60,
                )
            if r.status_code == 200:
                name = r.json().get("name") or "(no name)"
                print(f"  ✓  {pdf.name}  →  {name}")
                success.append(pdf.name)
            elif r.status_code == 409:
                print(f"  –  {pdf.name}  →  already exists (skipped)")
            else:
                print(f"  ✗  {pdf.name}  →  {r.status_code}: {r.text[:120]}")
                failed.append(pdf.name)
        except Exception as e:
            print(f"  ✗  {pdf.name}  →  {e}")
            failed.append(pdf.name)

        time.sleep(0.5)  # don't hammer the free tier

    print(f"\nDone — {len(success)} uploaded, {len(failed)} failed")
    if failed:
        print("Failed:", ", ".join(failed))

if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "."
    ingest_folder(folder)