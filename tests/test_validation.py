import unittest

from mcq_agent.models import PageText
from mcq_agent.validation import ValidationError, parse_model_json, validate_questions


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.pages = [
            PageText(1, "Photosynthesis converts light energy into chemical energy in plants."),
            PageText(2, "Mitochondria produce ATP through cellular respiration."),
        ]

    def valid_payload(self):
        return {
            "questions": [
                {
                    "question": "What does photosynthesis convert?",
                    "choices": {
                        "A": "Light energy into chemical energy",
                        "B": "ATP into oxygen",
                        "C": "Water into nitrogen",
                        "D": "Carbon into protein",
                    },
                    "answer": "A",
                    "citation": {
                        "page": 1,
                        "quote": "Photosynthesis converts light energy into chemical energy",
                    },
                }
            ]
        }

    def test_accepts_valid_grounded_question(self):
        questions = validate_questions(self.valid_payload(), 1, self.pages)

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].answer, "A")
        self.assertEqual(questions[0].citation.page, 1)

    def test_parses_json_wrapped_in_code_fence(self):
        payload = parse_model_json('```json\n{"questions": []}\n```')

        self.assertEqual(payload, {"questions": []})

    def test_rejects_wrong_question_count(self):
        with self.assertRaisesRegex(ValidationError, "Expected 2 questions"):
            validate_questions(self.valid_payload(), 2, self.pages)

    def test_rejects_duplicate_choices(self):
        payload = self.valid_payload()
        payload["questions"][0]["choices"]["B"] = "Light energy into chemical energy"

        with self.assertRaisesRegex(ValidationError, "distinct"):
            validate_questions(payload, 1, self.pages)

    def test_rejects_invalid_answer_label(self):
        payload = self.valid_payload()
        payload["questions"][0]["answer"] = "E"

        with self.assertRaisesRegex(ValidationError, "answer"):
            validate_questions(payload, 1, self.pages)

    def test_rejects_quote_not_found_on_cited_page(self):
        payload = self.valid_payload()
        payload["questions"][0]["citation"]["quote"] = "This sentence is not in the document."

        with self.assertRaisesRegex(ValidationError, "quote was not found"):
            validate_questions(payload, 1, self.pages)

    def test_rejects_page_not_in_source(self):
        payload = self.valid_payload()
        payload["questions"][0]["citation"]["page"] = 99

        with self.assertRaisesRegex(ValidationError, "not in the uploaded material"):
            validate_questions(payload, 1, self.pages)


if __name__ == "__main__":
    unittest.main()
