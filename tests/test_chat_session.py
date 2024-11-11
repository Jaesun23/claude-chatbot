import unittest
from unittest.mock import patch, MagicMock
from src.chat_session import ChatSession

class TestChatSession(unittest.TestCase):
    @patch('src.chat_session.Anthropic')
    def setUp(self, mock_anthropic):
        self.mock_client = MagicMock()
        mock_anthropic.return_value = self.mock_client
        self.chat_session = ChatSession()

    def test_add_message(self):
        self.chat_session.add_message("user", "Hello")
        self.assertEqual(len(self.chat_session.full_conversation_history), 1)
        self.assertEqual(self.chat_session.full_conversation_history[0]["role"], "user")
        self.assertEqual(self.chat_session.full_conversation_history[0]["content"], "Hello")

    def test_get_response(self):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Hello, how can I help you?")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        self.mock_client.messages.create.return_value = mock_response

        response = self.chat_session.get_response("Hi")
        self.assertEqual(response, "Hello, how can I help you?")
        self.assertEqual(self.chat_session.total_tokens_used, 30)

if __name__ == '__main__':
    unittest.main()