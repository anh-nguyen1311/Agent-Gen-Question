import json
import re
import unicodedata

from .models import CHOICE_LABELS, Citation, PageText, Question


class ValidationError(ValueError):
    pass


def parse_model_json(raw_text: str) -> dict:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValidationError("Gemini returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ValidationError("Gemini JSON must be an object.")
    return payload


def validate_questions(payload: dict, requested_count: int, source_pages: list[PageText]) -> list[Question]:
    raw_questions = payload.get("questions")
    if not isinstance(raw_questions, list):
        raise ValidationError("Gemini JSON must contain a questions list.")
    if len(raw_questions) != requested_count:
        raise ValidationError(f"Expected {requested_count} questions, got {len(raw_questions)}.")

    source_by_page = {page.page_number: page.text for page in source_pages}
    if not source_by_page:
        raise ValidationError("No source text is available for citation validation.")

    validated: list[Question] = []
    for index, item in enumerate(raw_questions, start=1):
        if not isinstance(item, dict):
            raise ValidationError(f"Question {index} must be an object.")

        question_text = _required_string(item, "question", index)
        choices = _validate_choices(item.get("choices"), index)
        answer = _required_string(item, "answer", index).upper()
        if answer not in CHOICE_LABELS:
            raise ValidationError(f"Question {index} answer must be one of A, B, C, or D.")

        citation = _validate_citation(item.get("citation"), index)
        page_text = source_by_page.get(citation.page)
        if page_text is None:
            raise ValidationError(f"Question {index} cites page {citation.page}, which is not in the uploaded material.")
        if _normalize(citation.quote) not in _normalize(page_text):
            raise ValidationError(f"Question {index} citation quote was not found on cited page {citation.page}.")

        validated.append(Question(question_text, choices, answer, citation))

    return validated


def _required_string(item: dict, field: str, question_index: int) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"Question {question_index} field {field} must be a non-empty string.")
    return value.strip()


def _validate_choices(raw_choices: object, question_index: int) -> dict[str, str]:
    if not isinstance(raw_choices, dict):
        raise ValidationError(f"Question {question_index} choices must be an object with A-D keys.")
    if set(raw_choices) != set(CHOICE_LABELS):
        raise ValidationError(f"Question {question_index} must have exactly choices A, B, C, and D.")

    choices: dict[str, str] = {}
    normalized_values = set()
    for label in CHOICE_LABELS:
        value = raw_choices[label]
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"Question {question_index} choice {label} must be a non-empty string.")
        clean_value = value.strip()
        choices[label] = clean_value
        normalized_values.add(_normalize(clean_value))

    if len(normalized_values) != 4:
        raise ValidationError(f"Question {question_index} choices must be distinct.")
    return choices


def _validate_citation(raw_citation: object, question_index: int) -> Citation:
    if not isinstance(raw_citation, dict):
        raise ValidationError(f"Question {question_index} citation must be an object.")
    page = raw_citation.get("page")
    if not isinstance(page, int) or page < 1:
        raise ValidationError(f"Question {question_index} citation page must be a positive integer.")
    quote = raw_citation.get("quote")
    if not isinstance(quote, str) or not quote.strip():
        raise ValidationError(f"Question {question_index} citation quote must be a non-empty string.")
    return Citation(page=page, quote=quote.strip())


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"\s+", " ", normalized).strip()
