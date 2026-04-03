from io import BytesIO

import pdfplumber
from pypdf import PdfReader

from app.services.extractors.base import ExtractionResult
from app.utils.text import clean_text


class PDFExtractor:
    def extract(self, file_bytes: bytes) -> ExtractionResult:
        buffer = BytesIO(file_bytes)
        reader = PdfReader(buffer)
        page_count = len(reader.pages)

        extracted_chunks: list[str] = []
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text(layout=True) or ""
                if text.strip():
                    extracted_chunks.append(text)

        if not extracted_chunks:
            for page in reader.pages:
                text = page.extract_text() or ""
                if text.strip():
                    extracted_chunks.append(text)

        return ExtractionResult(
            text=clean_text("\n".join(extracted_chunks)),
            detected_format="pdf",
            pages=page_count,
        )
