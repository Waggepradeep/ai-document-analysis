import base64
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings
from app.models.schemas import (
    DocumentAnalysisResponse,
    DocumentMetadata,
    SpecDocumentAnalysisResponse,
    SpecEntityGroup,
)
from app.services.analysis import AIAnalyzer
from app.services.extractors.base import UnsupportedFormatError
from app.services.extractors.factory import ExtractorFactory


class DocumentProcessor:
    FILE_TYPE_MAP = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc": "application/msword",
        "image": "image/png",
        "application/pdf": "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword": "application/msword",
        "image/png": "image/png",
        "image/jpeg": "image/jpeg",
        "image/jpg": "image/jpg",
        "image/webp": "image/webp",
        "image/tiff": "image/tiff",
        "image/bmp": "image/bmp",
    }

    def __init__(self) -> None:
        self.settings = get_settings()
        self.extractor_factory = ExtractorFactory()
        self.analyzer = AIAnalyzer()

    async def process(self, file: UploadFile) -> DocumentAnalysisResponse:
        file_bytes = await file.read()
        return self.process_bytes(
            filename=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream",
            file_bytes=file_bytes,
        )

    def process_bytes(self, filename: str, content_type: str, file_bytes: bytes) -> DocumentAnalysisResponse:
        max_bytes = self.settings.max_file_size_mb * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size of {self.settings.max_file_size_mb} MB.",
            )

        try:
            upload_proxy = type("UploadProxy", (), {"filename": filename, "content_type": content_type})()
            extractor = self.extractor_factory.get_extractor(upload_proxy)
            extraction = extractor.extract(file_bytes)
        except UnsupportedFormatError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

        if not extraction.text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No readable text could be extracted from the document.",
            )

        analysis = self.analyzer.analyze(extraction.text)
        metadata = DocumentMetadata(
            filename=filename,
            content_type=content_type,
            detected_format=extraction.detected_format,
            pages=extraction.pages,
            characters=len(extraction.text),
            extracted_at=datetime.now(timezone.utc),
        )
        return DocumentAnalysisResponse(metadata=metadata, content=extraction.text, analysis=analysis)

    def process_base64(self, filename: str, content_type: str, file_base64: str) -> SpecDocumentAnalysisResponse:
        normalized_type = self.FILE_TYPE_MAP.get(content_type.strip().lower())
        if not normalized_type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type.")

        try:
            file_bytes = base64.b64decode(file_base64, validate=True)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid base64 file.") from exc

        try:
            result = self.process_bytes(filename=filename, content_type=normalized_type, file_bytes=file_bytes)
        except HTTPException as exc:
            if exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
                return SpecDocumentAnalysisResponse(
                    status="error",
                    fileName=filename,
                    summary="",
                    entities=SpecEntityGroup(),
                    sentiment="Neutral",
                )
            raise

        return SpecDocumentAnalysisResponse(
            fileName=result.metadata.filename,
            summary=result.analysis.summary,
            entities=SpecEntityGroup(
                names=result.analysis.entities.names,
                dates=result.analysis.entities.dates,
                organizations=result.analysis.entities.organizations,
                amounts=result.analysis.entities.monetary_amounts,
            ),
            sentiment=result.analysis.sentiment.capitalize(),
        )
