from .models import PageText, Question
from .validation import ValidationError, parse_model_json, validate_questions


class GenerationError(RuntimeError):
    pass


def build_prompt(source_pages: list[PageText], question_count: int, max_source_chars: int) -> str:
    source_text = _bounded_source_text(source_pages, max_source_chars)
    return f"""
You generate multiple-choice questions from uploaded source material.

Rules:
- Generate exactly {question_count} questions.
- Use only the provided source material.
- Each question must test a key point from the source.
- Each question must have exactly four choices labeled A, B, C, and D.
- Exactly one choice must be undeniably correct based on the source.
- The incorrect choices must be plausible but clearly wrong based on the source.
- For every answer, include a citation with the page number and an exact quote copied from that page.
- Do not use outside knowledge.
- Do not invent facts, citations, page numbers, or quotes.

Return only valid JSON matching this schema:
{{
  "questions": [
    {{
      "question": "Question text",
      "choices": {{"A": "Choice A", "B": "Choice B", "C": "Choice C", "D": "Choice D"}},
      "answer": "A",
      "citation": {{"page": 1, "quote": "Exact supporting quote from the cited page"}}
    }}
  ]
}}

Source material:
{source_text}
""".strip()


def generate_questions(
    *,
    source_pages: list[PageText],
    question_count: int,
    project_id: str,
    location: str,
    model: str,
    max_source_chars: int,
) -> list[Question]:
    from google import genai
    from google.genai import types

    client = genai.Client(vertexai=True, project=project_id, location=location)
    prompt = build_prompt(source_pages, question_count, max_source_chars)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )
    raw_text = getattr(response, "text", None)
    if not raw_text:
        raise GenerationError("Gemini returned an empty response.")

    try:
        payload = parse_model_json(raw_text)
        return validate_questions(payload, question_count, source_pages)
    except ValidationError as exc:
        raise GenerationError(str(exc)) from exc


def _bounded_source_text(source_pages: list[PageText], max_source_chars: int) -> str:
    chunks: list[str] = []
    remaining = max_source_chars
    for page in source_pages:
        if remaining <= 0:
            break
        header = f"[Page {page.page_number}]\n"
        text = page.text.strip()
        chunk = header + text
        if len(chunk) > remaining:
            chunk = chunk[:remaining]
        chunks.append(chunk)
        remaining -= len(chunk)
    return "\n\n".join(chunks)
