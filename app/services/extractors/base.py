from dataclasses import dataclass


@dataclass
class ExtractionResult:
    text: str
    detected_format: str
    pages: int | None = None


class UnsupportedFormatError(ValueError):
    """Raised when a file type is not supported."""
