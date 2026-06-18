import unittest

from mcq_agent.formatting import format_questions_for_display
from mcq_agent.models import Citation, Question


class FormattingTests(unittest.TestCase):
    def test_formats_questions_with_answers_at_bottom(self):
        output = format_questions_for_display(
            [
                Question(
                    text="What is the key fact?",
                    choices={"A": "Alpha", "B": "Beta", "C": "Gamma", "D": "Delta"},
                    answer="B",
                    citation=Citation(page=2, quote="Beta is the key fact."),
                )
            ]
        )

        self.assertIn("1. What is the key fact?", output)
        self.assertIn("   A. Alpha", output)
        self.assertIn("Answers", output)
        self.assertIn('1. B. Beta (Page 2: "Beta is the key fact.")', output)


if __name__ == "__main__":
    unittest.main()
