import unittest
from src.utils import count_tokens, generate_message_id, truncate_conversation

class TestUtils(unittest.TestCase):
    def test_count_tokens(self):
        messages = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm fine, thank you!"}
        ]
        token_count = count_tokens(messages)
        self.assertEqual(token_count, 9)  # 5 + 4 tokens

    def test_generate_message_id(self):
        id1 = generate_message_id()
        id2 = generate_message_id()
        self.assertNotEqual(id1, id2)

    def test_truncate_conversation(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you for asking."}
        ]
        truncated = truncate_conversation(messages, 5)
        self.assertEqual(len(truncated), 2)
        self.assertEqual(truncated[-1]["content"], "How are you?")

if __name__ == '__main__':
    unittest.main()