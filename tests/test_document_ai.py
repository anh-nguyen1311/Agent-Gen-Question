from types import SimpleNamespace
import unittest

from mcq_agent.document_ai import detect_mime_type, document_to_page_texts, text_from_anchor


def segment(start, end):
    return SimpleNamespace(start_index=start, end_index=end)


def page_with_segments(*segments):
    return SimpleNamespace(
        layout=SimpleNamespace(text_anchor=SimpleNamespace(text_segments=list(segments)))
    )


class DocumentAiHelperTests(unittest.TestCase):
    def test_detects_supported_mime_types(self):
        self.assertEqual(detect_mime_type("lesson.PDF"), "application/pdf")
        self.assertEqual(
            detect_mime_type("notes.docx"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    def test_extracts_text_from_anchor_segments(self):
        full_text = "First page text. Second page text."

        self.assertEqual(text_from_anchor(full_text, SimpleNamespace(text_segments=[segment(0, 16)])), "First page text.")

    def test_converts_document_pages_to_page_texts(self):
        full_text = "First page text. Second page text."
        first_end = len("First page text.")
        document = SimpleNamespace(
            text=full_text,
            pages=[
                page_with_segments(segment(0, first_end)),
                page_with_segments(segment(first_end + 1, len(full_text))),
            ],
        )

        pages = document_to_page_texts(document)

        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0].page_number, 1)
        self.assertEqual(pages[0].text, "First page text.")
        self.assertEqual(pages[1].page_number, 2)
        self.assertEqual(pages[1].text, "Second page text.")

    def test_falls_back_to_full_text_when_pages_are_missing(self):
        document = SimpleNamespace(text="Only full document text.", pages=[])

        pages = document_to_page_texts(document)

        self.assertEqual(pages[0].page_number, 1)
        self.assertEqual(pages[0].text, "Only full document text.")


if __name__ == "__main__":
    unittest.main()
