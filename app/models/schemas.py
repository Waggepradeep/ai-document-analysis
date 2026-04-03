from datetime import datetime

from pydantic import BaseModel, Field


class EntityGroup(BaseModel):
    names: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    monetary_amounts: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)
    phone_numbers: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    summary: str
    sentiment: str
    entities: EntityGroup
    keywords: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class DocumentMetadata(BaseModel):
    filename: str
    content_type: str
    detected_format: str
    pages: int | None = None
    characters: int
    extracted_at: datetime


class DocumentAnalysisResponse(BaseModel):
    metadata: DocumentMetadata
    content: str
    analysis: AnalysisResult


class Base64DocumentRequest(BaseModel):
    fileName: str
    fileType: str
    fileBase64: str


class SpecEntityGroup(BaseModel):
    names: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    amounts: list[str] = Field(default_factory=list)


class SpecDocumentAnalysisResponse(BaseModel):
    status: str = "success"
    fileName: str
    summary: str
    entities: SpecEntityGroup
    sentiment: str
