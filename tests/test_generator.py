import unittest

from mcq_agent.generator import build_prompt
from mcq_agent.models import PageText


class GeneratorPromptTests(unittest.TestCase):
    def test_prompt_contains_count_rules_and_page_markers(self):
        prompt = build_prompt([PageText(3, "Key source fact.")], 4, 1000)

        self.assertIn("Generate exactly 4 questions", prompt)
        self.assertIn("[Page 3]", prompt)
        self.assertIn("Key source fact.", prompt)
        self.assertIn("Do not invent facts", prompt)

    def test_prompt_respects_source_character_limit(self):
        prompt = build_prompt([PageText(1, "A" * 100), PageText(2, "B" * 100)], 1, 30)

        self.assertIn("[Page 1]", prompt)
        self.assertNotIn("[Page 2]", prompt)


if __name__ == "__main__":
    unittest.main()
