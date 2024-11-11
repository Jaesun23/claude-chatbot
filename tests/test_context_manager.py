import unittest
from src.context_manager import ContextManager

class TestContextManager(unittest.TestCase):
    def setUp(self):
        """각 테스트 전에 실행됩니다."""
        self.context_manager = ContextManager()

    def test_initialization(self):
        """초기화 상태 테스트"""
        # 기본 컨텍스트가 모두 있는지 확인
        for context in ContextManager.DEFAULT_CONTEXTS.keys():
            self.assertIn(context, self.context_manager.system_prompts)
            
        # 기본 상태 확인
        self.assertEqual(self.context_manager.active_context, "general")
        self.assertEqual(len(self.context_manager.context_history), 0)

    def test_set_context(self):
        """컨텍스트 설정 테스트"""
        # 유효한 컨텍스트 설정
        prompt = self.context_manager.set_context("code_review")
        self.assertEqual(self.context_manager.active_context, "code_review")
        self.assertIn("Python developer", prompt)
        self.assertEqual(len(self.context_manager.context_history), 1)
        
        # 잘못된 컨텍스트 설정 시도
        with self.assertRaises(ValueError):
            self.context_manager.set_context("nonexistent_context")

    def test_context_history(self):
        """컨텍스트 히스토리 관리 테스트"""
        # 여러 컨텍스트 변경
        contexts = ["teacher", "translator", "writer", "general", "code_review"]
        for context in contexts:
            self.context_manager.set_context(context)
            
        history = self.context_manager.get_context_history()
        
        # 히스토리 검증
        self.assertEqual(len(history), 5)
        self.assertEqual(history, contexts)
        
        # 최대 히스토리 제한 테스트
        max_history = self.context_manager.max_history
        for i in range(max_history + 5):
            self.context_manager.set_context("general")
            
        self.assertLessEqual(len(self.context_manager.context_history), max_history)

    def test_add_custom_context(self):
        """커스텀 컨텍스트 추가 테스트"""
        # 새로운 컨텍스트 추가
        self.context_manager.add_custom_context("custom", "This is a custom prompt")
        self.assertIn("custom", self.context_manager.system_prompts)
        self.assertEqual(
            self.context_manager.system_prompts["custom"],
            "This is a custom prompt"
        )
        
        # 기본 컨텍스트 덮어쓰기 시도
        with self.assertRaises(ValueError):
            self.context_manager.add_custom_context("general", "New general prompt")

    def test_get_current_system_prompt(self):
        """현재 시스템 프롬프트 반환 테스트"""
        # 기본 컨텍스트
        self.assertEqual(
            self.context_manager.get_current_system_prompt(),
            ContextManager.DEFAULT_CONTEXTS["general"]
        )
        
        # 컨텍스트 변경 후
        self.context_manager.set_context("teacher")
        self.assertEqual(
            self.context_manager.get_current_system_prompt(),
            ContextManager.DEFAULT_CONTEXTS["teacher"]
        )
        
        # 커스텀 컨텍스트 추가 후
        custom_prompt = "Custom prompt for testing"
        self.context_manager.add_custom_context("test", custom_prompt)
        self.context_manager.set_context("test")
        self.assertEqual(
            self.context_manager.get_current_system_prompt(),
            custom_prompt
        )

    def test_get_available_contexts(self):
        """사용 가능한 컨텍스트 목록 테스트"""
        # 기본 컨텍스트 확인
        contexts = self.context_manager.get_available_contexts()
        for default_context in ContextManager.DEFAULT_CONTEXTS:
            self.assertIn(default_context, contexts)
            
        # 커스텀 컨텍스트 추가 후 확인
        self.context_manager.add_custom_context("custom1", "Prompt 1")
        self.context_manager.add_custom_context("custom2", "Prompt 2")
        
        updated_contexts = self.context_manager.get_available_contexts()
        self.assertIn("custom1", updated_contexts)
        self.assertIn("custom2", updated_contexts)

if __name__ == '__main__':
    unittest.main()