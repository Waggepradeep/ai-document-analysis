from fastapi import UploadFile

from app.services.extractors.base import UnsupportedFormatError
from app.services.extractors.docx import DOCXExtractor
from app.services.extractors.image import ImageExtractor
from app.services.extractors.pdf import PDFExtractor


class ExtractorFactory:
    PDF_TYPES = {"application/pdf"}
    DOCX_TYPES = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }
    IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/tiff", "image/bmp"}

    def get_extractor(self, upload: UploadFile):
        content_type = (upload.content_type or "").lower()
        filename = (upload.filename or "").lower()

        if content_type in self.PDF_TYPES or filename.endswith(".pdf"):
            return PDFExtractor()
        if content_type in self.DOCX_TYPES or filename.endswith(".docx") or filename.endswith(".doc"):
            return DOCXExtractor()
        if content_type in self.IMAGE_TYPES or filename.endswith(
            (".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp")
        ):
            return ImageExtractor()

        raise UnsupportedFormatError(f"Unsupported file format: {upload.content_type or upload.filename}")
