from io import BytesIO
from pathlib import Path
import sys
import base64

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app

client = TestClient(app)
API_HEADERS = {"x-api-key": "your-secret-api-key"}


def test_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_rejects_unsupported_format() -> None:
    response = client.post(
        "/api/v1/documents/analyze",
        files={"file": ("sample.txt", b"hello", "text/plain")},
        headers=API_HEADERS,
    )
    assert response.status_code == 400


def test_rejects_missing_api_key() -> None:
    response = client.post("/api/document-analyze", json={"fileName": "a.pdf", "fileType": "application/pdf", "fileBase64": "aGVsbG8="})
    assert response.status_code == 422 or response.status_code == 401


def test_rejects_invalid_base64() -> None:
    response = client.post(
        "/api/document-analyze",
        json={"fileName": "a.pdf", "fileType": "pdf", "fileBase64": "%%%bad%%%"},
        headers=API_HEADERS,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid base64 file."


def test_rejects_invalid_file_type() -> None:
    response = client.post(
        "/api/document-analyze",
        json={"fileName": "a.pdf", "fileType": "spreadsheet", "fileBase64": "aGVsbG8="},
        headers=API_HEADERS,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported file type."


def test_accepts_image_document(monkeypatch) -> None:
    monkeypatch.setattr("app.services.extractors.image.pytesseract.image_to_string", lambda _image: "Invoice Amount $450 Due 12/12/2026")

    image = Image.new("RGB", (500, 180), "white")
    drawer = ImageDraw.Draw(image)
    drawer.text((20, 60), "Invoice Amount $450 Due 12/12/2026", fill="black")

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    response = client.post(
        "/api/v1/documents/analyze",
        files={"file": ("invoice.png", buffer.getvalue(), "image/png")},
        headers=API_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["detected_format"] == "image"
    assert "summary" in payload["analysis"]


def test_base64_spec_endpoint(monkeypatch) -> None:
    monkeypatch.setattr("app.services.extractors.image.pytesseract.image_to_string", lambda _image: "Invoice Amount $450 Due 12/12/2026")

    image = Image.new("RGB", (500, 180), "white")
    drawer = ImageDraw.Draw(image)
    drawer.text((20, 60), "Invoice Amount $450 Due 12/12/2026", fill="black")

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    payload = {
        "fileName": "invoice.png",
        "fileType": "image",
        "fileBase64": base64.b64encode(buffer.getvalue()).decode("utf-8"),
    }
    response = client.post("/api/document-analyze", json=payload, headers=API_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"status", "fileName", "summary", "entities", "sentiment"}
    assert set(body["entities"].keys()) == {"names", "dates", "organizations", "amounts"}
    assert body["status"] == "success"


def test_empty_text_returns_error_payload(monkeypatch) -> None:
    monkeypatch.setattr("app.services.extractors.image.pytesseract.image_to_string", lambda _image: "   ")

    image = Image.new("RGB", (200, 100), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    payload = {
        "fileName": "blank.png",
        "fileType": "image",
        "fileBase64": base64.b64encode(buffer.getvalue()).decode("utf-8"),
    }
    response = client.post("/api/document-analyze", json=payload, headers=API_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["summary"] == ""
    assert body["entities"] == {"names": [], "dates": [], "organizations": [], "amounts": []}
    assert body["sentiment"] == "Neutral"
