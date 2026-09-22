from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from app.core.database import SessionLocal
from app.resume.extraction import extract_pdf_text
from app.resume.parser import extract_resume_profile


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose InternAI resume extraction locally.")
    parser.add_argument("pdf_path", type=Path)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    text = extract_pdf_text(args.pdf_path)
    with SessionLocal() as db:
        profile, method = extract_resume_profile(text, db)
    print(json.dumps({"extraction_method": method, "draft_profile": profile}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
