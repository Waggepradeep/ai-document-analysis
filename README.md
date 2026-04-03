# AI Document Analysis API

Production-style document analysis API for the GUVI Hackathon AI-Powered Document Analysis & Extraction track.

The service accepts `PDF`, `DOCX`, and image files, extracts readable text, then returns:
- summary
- named entities
- sentiment
- OCR-backed extraction for image documents

## Live Project

- Live URL: `https://ai-document-analysis-wh9b.onrender.com`
- API Docs: `https://ai-document-analysis-wh9b.onrender.com/docs`
- GitHub Repo: `https://github.com/Waggepradeep/ai-document-analysis`

## Features

- Multi-format support: `PDF`, `DOCX`, `PNG`, `JPG`, `JPEG`, `TIFF`, `BMP`, `WEBP`
- OCR for images using Tesseract
- Layout-aware PDF extraction with `pdfplumber`
- AI-powered summary, entity extraction, and sentiment analysis using Gemini
- Rule-based fallback if the AI provider is unavailable
- Spec-compatible base64 endpoint for hackathon evaluation
- Rich multipart endpoint for debugging and manual testing
- API-key protected endpoints

## Architecture Overview

The project is organized into a small service-oriented FastAPI backend:

- [app/main.py](c:\Users\wagge\OneDrive\Desktop\ai-document-analysis-api\app\main.py)
  Defines the FastAPI app, root route, and health route.
- [documents.py](c:\Users\wagge\OneDrive\Desktop\ai-document-analysis-api\app\api\routes\documents.py)
  Exposes the two API routes.
- [document_processor.py](c:\Users\wagge\OneDrive\Desktop\ai-document-analysis-api\app\services\document_processor.py)
  Handles input validation, extraction, analysis, and spec-response formatting.
- [analysis.py](c:\Users\wagge\OneDrive\Desktop\ai-document-analysis-api\app\services\analysis.py)
  Runs Gemini-backed document analysis and applies small entity cleanup rules.
- [extractors](c:\Users\wagge\OneDrive\Desktop\ai-document-analysis-api\app\services\extractors)
  Contains separate extractors for PDF, DOCX, and image files.

## Tech Stack

- Backend: FastAPI
- Runtime: Python 3.12
- OCR: Tesseract + `pytesseract`
- PDF extraction: `pdfplumber`, `pypdf`
- DOCX extraction: `python-docx`
- AI model: Gemini `gemini-2.5-flash`
- Deployment: Docker + Render
- Testing: `pytest`

## API Endpoints

### `POST /api/document-analyze`

Primary hackathon/spec endpoint.

Request:
- header: `x-api-key`
- JSON body:

```json
{
  "fileName": "sample.pdf",
  "fileType": "pdf",
  "fileBase64": "BASE64_ENCODED_FILE_CONTENT"
}
```

Response:

```json
{
  "status": "success",
  "fileName": "sample.pdf",
  "summary": "Short summary...",
  "entities": {
    "names": ["John Doe"],
    "dates": ["2026-04-03"],
    "organizations": ["Example University"],
    "amounts": ["$500"]
  },
  "sentiment": "Positive"
}
```

### `POST /api/v1/documents/analyze`

Rich multipart endpoint for debugging and testing.

Request:
- header: `x-api-key`
- form-data:
  - `file`

This route returns extracted text plus a richer analysis payload, including locations, emails, phone numbers, and confidence.

### `GET /`

Simple root route for deployed environments.

### `GET /health`

Health check.

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Useful URLs:
- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

## Environment Variables

```env
APP_NAME=AI Document Analysis API
APP_ENV=development
API_KEY=your-secret-api-key
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
OPENAI_TIMEOUT_SECONDS=30
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
MAX_FILE_SIZE_MB=20
```

Notes:
- `API_KEY` is required by both API routes through the `x-api-key` header.
- `GEMINI_API_KEY` powers the AI analysis path.
- `TESSERACT_CMD` is mainly needed for local Windows development. In Docker/Render, Tesseract is installed in the container.

## Deployment

### Docker

```bash
docker build -t ai-document-analysis-api .
docker run -p 8000:8000 --env-file .env ai-document-analysis-api
```

### Render

This repository includes:
- [Dockerfile](c:\Users\wagge\OneDrive\Desktop\ai-document-analysis-api\Dockerfile)
- [render.yaml](c:\Users\wagge\OneDrive\Desktop\ai-document-analysis-api\render.yaml)

Deployment steps:
1. Connect the GitHub repository in Render.
2. Deploy as a Docker web service.
3. Set environment variables in Render dashboard.
4. Use the public service URL for hackathon submission.

## Testing

```bash
pytest
```

Current local verification:
- API routes working
- OCR tested on image sample
- PDF, DOCX, and image flows validated
- Endpoint tester passed successfully

## AI Tools Used

This project uses AI in two ways:

- Gemini API
  Used for document summarization, entity extraction, and sentiment analysis.
- AI coding assistance during development
  Used to help structure implementation, refine prompts, improve entity cleanup, and prepare documentation.

## Known Limitations

- Entity extraction depends on OCR/text quality for scanned or noisy image inputs.
- Some documents with very generic wording may return fewer named organizations if the text does not contain strong named entities.
- Rule-based fallback is less accurate than the Gemini path.
- Extremely long documents are truncated before LLM analysis to keep inference practical and stable.
- The spec endpoint intentionally returns a reduced response shape compared to the richer multipart route.

## Submission Notes

For the hackathon submission, use:
- Live URL: `https://ai-document-analysis-wh9b.onrender.com`
- Endpoint URL: `https://ai-document-analysis-wh9b.onrender.com/api/document-analyze`
- API key header: `x-api-key`
- GitHub repo: `https://github.com/Waggepradeep/ai-document-analysis`

The project was built for the `AI-Powered Document Analysis & Extraction` problem statement and tested against PDF, DOCX, and image inputs.
