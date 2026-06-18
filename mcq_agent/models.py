from dataclasses import dataclass

CHOICE_LABELS = ("A", "B", "C", "D")


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


@dataclass(frozen=True)
class Citation:
    page: int
    quote: str


@dataclass(frozen=True)
class Question:
    text: str
    choices: dict[str, str]
    answer: str
    citation: Citation
