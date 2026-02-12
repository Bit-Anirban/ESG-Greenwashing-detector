from pathlib import Path
import PyPDF2

def extract_text_from_pdf(pdf_path: str) -> str:
    pdf_path = Path(pdf_path)
    text = []

    with pdf_path.open("rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)

    return "\n".join(text)
