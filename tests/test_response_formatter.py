import unittest
from src.response_formatter import format_response

class TestResponseFormatter(unittest.TestCase):
    def test_code_block_formatting(self):
        input_text = "Here's some code:\n```python\nprint('Hello, World!')\n```"
        formatted = format_response(input_text)
        self.assertIn("print('Hello, World!')", formatted)
        self.assertNotIn("```python", formatted)

    def test_bold_formatting(self):
        input_text = "This is **bold** text."
        formatted = format_response(input_text)
        self.assertIn("\033[1m", formatted)
        self.assertIn("\033[0m", formatted)

    def test_italic_formatting(self):
        input_text = "This is *italic* text."
        formatted = format_response(input_text)
        self.assertIn("\033[3m", formatted)
        self.assertIn("\033[0m", formatted)

if __name__ == '__main__':
    unittest.main()