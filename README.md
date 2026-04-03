# AI Document Analysis API

An async document-processing API that extracts text from `PDF`, `DOCX`, and image files, then returns:

- document text
- concise summary
- named entities
- sentiment
- keywords

The service is designed so you can plug in a stronger AI model for better scoring while still keeping a no-hardcoded local fallback.

## Features

- Multi-format support: PDF, DOCX, PNG, JPG, JPEG, TIFF, BMP, WEBP
- OCR for image-based documents using Tesseract
- Layout-aware PDF extraction with `pdfplumber`
- AI-powered analysis through OpenAI when `OPENAI_API_KEY` is set
- Deterministic fallback summarization, entity extraction, and sentiment analysis when no API key is available
- Async FastAPI endpoint ready for Docker or Render deployment

## API

### `POST /api/document-analyze`

Primary spec-compatible endpoint. Send JSON with `fileName`, `fileType`, and `fileBase64`, plus the `x-api-key` header.
`fileType` can be either `pdf`, `docx`, `image` or a MIME type such as `application/pdf`.

Example request:

```json
{
  "fileName": "sample.pdf",
  "fileType": "application/pdf",
  "fileBase64": "BASE64_ENCODED_FILE_CONTENT"
}
```

Example response:

```json
{
  "status": "success",
  "fileName": "sample.pdf",
  "summary": "Concise factual summary...",
  "entities": {
    "names": ["John Doe"],
    "dates": ["Jan 10, 2026"],
    "organizations": ["Acme Corporation"],
    "amounts": ["$450"]
  },
  "sentiment": "Neutral"
}
```

### `POST /api/v1/documents/analyze`

Compatibility endpoint for multipart uploads with a `file` field. This returns a richer debugging response and also requires `x-api-key`.

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

Swagger UI:

```text
http://localhost:8000/docs
```

## Environment variables

- `OPENAI_API_KEY`: optional, enables LLM analysis
- `API_KEY`: required request header value for `x-api-key`
- `OPENAI_MODEL`: defaults to `gpt-4.1-mini`
- `OPENAI_TIMEOUT_SECONDS`: timeout for AI calls before falling back safely
- `TESSERACT_CMD`: optional custom path to the Tesseract binary
- `MAX_FILE_SIZE_MB`: upload limit

## Deployment

### Docker

```bash
docker build -t ai-document-analysis-api .
docker run -p 8000:8000 --env-file .env ai-document-analysis-api
```

### Render

This repo includes a `render.yaml` so it can be deployed as a Docker web service. Set `OPENAI_API_KEY` and any other env vars in the Render dashboard.

## Notes for submission

- Public deployment URL: deploy this service to Render, Railway, Fly.io, or similar
- API key: expose your deployed endpoint or protected key according to the challenge instructions
- GitHub repository: initialize git and push this folder to a new repository

## Testing

```bash
pytest
```
