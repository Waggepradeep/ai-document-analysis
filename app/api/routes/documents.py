from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.models.schemas import Base64DocumentRequest, DocumentAnalysisResponse, SpecDocumentAnalysisResponse
from app.services.document_processor import DocumentProcessor

router = APIRouter(tags=["documents"])
processor = DocumentProcessor()
settings = get_settings()


def verify_api_key(x_api_key: str = Header(..., alias="x-api-key")) -> None:
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


@router.post("/api/v1/documents/analyze", response_model=DocumentAnalysisResponse, dependencies=[Depends(verify_api_key)])
async def analyze_document(file: UploadFile = File(...)) -> DocumentAnalysisResponse:
    return await processor.process(file)


@router.post("/api/document-analyze", response_model=SpecDocumentAnalysisResponse, dependencies=[Depends(verify_api_key)])
async def analyze_document_base64(payload: Base64DocumentRequest) -> SpecDocumentAnalysisResponse:
    return processor.process_base64(
        filename=payload.fileName,
        content_type=payload.fileType,
        file_base64=payload.fileBase64,
    )
