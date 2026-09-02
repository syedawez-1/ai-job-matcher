"""
Extract raw text from resume PDFs and structure it into skills,
education, projects, and experience using the AI client.
"""

import pdfplumber

from app.services import ai_client


def extract_text(file_path: str) -> str:
    text_chunks = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)
    return "\n".join(text_chunks)


def parse_resume(file_path: str) -> dict:
    raw_text = extract_text(file_path)
    structured = ai_client.structure_resume(raw_text)
    structured["raw_text"] = raw_text
    return structured
