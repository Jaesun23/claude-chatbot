import unittest
import os
import shutil
from src.conversation_manager import ConversationManager

class TestConversationManager(unittest.TestCase):
    def setUp(self):
        self.test_storage_dir = "test_conversations"
        self.manager = ConversationManager(storage_dir=self.test_storage_dir)

    def tearDown(self):
        if os.path.exists(self.test_storage_dir):
            shutil.rmtree(self.test_storage_dir)

    def test_create_new_session(self):
        session = self.manager.create_new_session("test_session")
        self.assertIsNotNone(session)
        self.assertEqual(self.manager.current_session, session)

    def test_switch_session(self):
        self.manager.create_new_session("session1")
        self.manager.create_new_session("session2")
        self.manager.switch_session("session1")
        self.assertEqual(self.manager.current_session, self.manager.sessions["session1"])

    def test_save_and_load_session(self):
        original_session = self.manager.create_new_session("test_session")
        original_session.add_message("user", "Hello")
        self.manager.save_session("test_session")

        loaded_session = self.manager.load_session("test_session")
        self.assertEqual(len(loaded_session.full_conversation_history), 1)
        self.assertEqual(loaded_session.full_conversation_history[0]["content"], "Hello")

if __name__ == '__main__':
    unittest.main()