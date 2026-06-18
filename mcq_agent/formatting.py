from .models import CHOICE_LABELS, Question


def format_questions_for_display(questions: list[Question]) -> str:
    lines: list[str] = []
    for index, question in enumerate(questions, start=1):
        lines.append(f"{index}. {question.text}")
        for label in CHOICE_LABELS:
            lines.append(f"   {label}. {question.choices[label]}")
        lines.append("")

    lines.append("Answers")
    lines.append("-------")
    for index, question in enumerate(questions, start=1):
        answer_text = question.choices[question.answer]
        lines.append(
            f"{index}. {question.answer}. {answer_text} "
            f"(Page {question.citation.page}: \"{question.citation.quote}\")"
        )
    return "\n".join(lines).strip()
