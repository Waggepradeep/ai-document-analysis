from io import BytesIO

from PIL import Image
import pytesseract

from app.core.config import get_settings
from app.services.extractors.base import ExtractionResult
from app.utils.text import clean_text


class ImageExtractor:
    def __init__(self) -> None:
        settings = get_settings()
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    def extract(self, file_bytes: bytes) -> ExtractionResult:
        image = Image.open(BytesIO(file_bytes))
        text = pytesseract.image_to_string(image)
        return ExtractionResult(
            text=clean_text(text),
            detected_format="image",
            pages=1,
        )
