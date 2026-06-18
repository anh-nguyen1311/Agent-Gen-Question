from collections.abc import Iterable
import io
from pathlib import Path

from .models import PageText


SUPPORTED_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class DocumentExtractionError(ValueError):
    pass


def detect_mime_type(file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()
    try:
        return SUPPORTED_MIME_TYPES[suffix]
    except KeyError as exc:
        raise DocumentExtractionError("Upload a PDF or Word .docx file.") from exc


def validate_upload_size(file_bytes: bytes, max_upload_mb: int) -> None:
    max_bytes = max_upload_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise DocumentExtractionError(f"File is larger than the {max_upload_mb} MB limit.")


def count_pdf_pages(file_bytes: bytes) -> int | None:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        return len(reader.pages)
    except Exception:
        return None


def extract_text_with_document_ai(
    *,
    file_bytes: bytes,
    mime_type: str,
    project_id: str,
    location: str,
    processor_id: str,
    max_pages: int,
) -> list[PageText]:
    from google.api_core.client_options import ClientOptions
    from google.cloud import documentai

    endpoint = f"{location}-documentai.googleapis.com"
    client = documentai.DocumentProcessorServiceClient(client_options=ClientOptions(api_endpoint=endpoint))
    processor_name = client.processor_path(project_id, location, processor_id)
    raw_document = documentai.RawDocument(content=file_bytes, mime_type=mime_type)
    request = documentai.ProcessRequest(name=processor_name, raw_document=raw_document)

    result = client.process_document(request=request)
    pages = document_to_page_texts(result.document)
    if len(pages) > max_pages:
        raise DocumentExtractionError(f"Document has {len(pages)} pages, above the {max_pages} page limit.")
    return pages


def document_to_page_texts(document: object) -> list[PageText]:
    full_text = getattr(document, "text", "") or ""
    raw_pages = list(getattr(document, "pages", []) or [])
    pages: list[PageText] = []

    for index, page in enumerate(raw_pages, start=1):
        layout = getattr(page, "layout", None)
        text_anchor = getattr(layout, "text_anchor", None) if layout else None
        page_text = text_from_anchor(full_text, text_anchor).strip()
        if page_text:
            pages.append(PageText(index, page_text))

    if not pages and full_text.strip():
        pages.append(PageText(1, full_text.strip()))

    if not pages:
        raise DocumentExtractionError("Document AI did not return extractable text.")
    return pages


def text_from_anchor(full_text: str, text_anchor: object | None) -> str:
    if not text_anchor:
        return ""
    segments: Iterable[object] = getattr(text_anchor, "text_segments", []) or []
    chunks: list[str] = []
    for segment in segments:
        start = int(getattr(segment, "start_index", 0) or 0)
        end = int(getattr(segment, "end_index", 0) or 0)
        if end > start:
            chunks.append(full_text[start:end])
    return "".join(chunks)
