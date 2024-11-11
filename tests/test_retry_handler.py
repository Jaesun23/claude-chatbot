import unittest
import asyncio
from unittest.mock import MagicMock, patch
from src.retry_handler import RetryHandler
import time

class TestRetryHandler(unittest.TestCase):
    def setUp(self):
        """각 테스트 전에 실행됩니다."""
        self.retry_handler = RetryHandler(max_retries=3, base_delay=0.1)

    def test_calculate_delay(self):
        """지수 백오프 지연 시간 계산 테스트"""
        # 지터 없이 정확한 지연 시간 테스트
        self.assertEqual(self.retry_handler.calculate_delay(0, jitter=False), 0.1)
        self.assertEqual(self.retry_handler.calculate_delay(1, jitter=False), 0.2)
        self.assertEqual(self.retry_handler.calculate_delay(2, jitter=False), 0.4)
        
        # 지터가 있는 경우 범위 테스트
        for attempt in range(3):
            delay = self.retry_handler.calculate_delay(attempt, jitter=True)
            base_delay = 0.1 * (2 ** attempt)
            self.assertGreaterEqual(delay, base_delay * 0.5)
            self.assertLessEqual(delay, base_delay * 1.5)

    def test_error_handler_registration(self):
        """에러 핸들러 등록 테스트"""
        handler = MagicMock()
        self.retry_handler.register_error_handler(ValueError, handler)
        
        self.assertIn(ValueError, self.retry_handler.error_handlers)
        self.assertEqual(self.retry_handler.error_handlers[ValueError], handler)

    def test_retry_decorator(self):
        """재시도 데코레이터 테스트"""
        mock_func = MagicMock(side_effect=[ValueError, ValueError, "success"])
        
        @self.retry_handler.retry
        def test_function():
            return mock_func()
            
        # 함수 실행
        result = test_function()
        
        # 검증
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)

    def test_retry_decorator_failure(self):
        """최대 재시도 횟수 초과 테스트"""
        mock_func = MagicMock(side_effect=ValueError("Test error"))
        
        @self.retry_handler.retry
        def test_function():
            return mock_func()
            
        # 예외 발생 확인
        with self.assertRaises(ValueError):
            test_function()
            
        # 정확한 재시도 횟수 확인
        self.assertEqual(mock_func.call_count, self.retry_handler.max_retries)

    async def async_test_function(self, mock_func):
        """비동기 테스트를 위한 헬퍼 함수"""
        return await self.retry_handler.async_retry(mock_func)

    def test_async_retry(self):
        """비동기 재시도 로직 테스트"""
        async def run_async_test():
            # 성공 케이스 테스트
            mock_success = MagicMock(side_effect=[ValueError, ValueError, "success"])
            result = await self.async_test_function(mock_success)
            self.assertEqual(result, "success")
            self.assertEqual(mock_success.call_count, 3)
            
            # 실패 케이스 테스트
            mock_failure = MagicMock(side_effect=ValueError("Test error"))
            with self.assertRaises(ValueError):
                await self.async_test_function(mock_failure)
            self.assertEqual(mock_failure.call_count, self.retry_handler.max_retries)

        # 비동기 테스트 실행
        asyncio.run(run_async_test())

    def test_is_retryable_error(self):
        """재시도 가능한 에러 판단 테스트"""
        # API 에러 모의 객체 생성
        class MockAPIError(Exception):
            def __init__(self, status_code):
                self.status_code = status_code
        
        # 재시도 가능한 에러 테스트
        retryable_errors = [
            MockAPIError(429),  # Rate limit
            MockAPIError(500),  # Server error
            MockAPIError(503)   # Service unavailable
        ]
        
        for error in retryable_errors:
            with patch('anthropic.APIError', MockAPIError):
                self.assertTrue(
                    self.retry_handler.is_retryable_error(error),
                    f"Status code {error.status_code} should be retryable"
                )
        
        # 재시도 불가능한 에러 테스트
        non_retryable_errors = [
            MockAPIError(400),  # Bad request
            MockAPIError(401),  # Unauthorized
            MockAPIError(404),  # Not found
            ValueError("Test error")
        ]
        
        for error in non_retryable_errors:
            with patch('anthropic.APIError', MockAPIError):
                self.assertFalse(
                    self.retry_handler.is_retryable_error(error),
                    f"Error {error} should not be retryable"
                )

    def test_error_handler_execution(self):
        """에러 핸들러 실행 테스트"""
        # 에러 핸들러 모의 객체
        mock_handler = MagicMock()
        self.retry_handler.register_error_handler(ValueError, mock_handler)
        
        # 테스트 함수
        mock_func = MagicMock(side_effect=[ValueError("Test error"), "success"])
        
        @self.retry_handler.retry
        def test_function():
            return mock_func()
        
        # 함수 실행
        result = test_function()
        
        # 검증
        self.assertEqual(result, "success")
        mock_handler.assert_called_once()
        args = mock_handler.call_args[0]
        self.assertIsInstance(args[0], ValueError)
        self.assertEqual(args[1], 0)  # 첫 번째 시도

if __name__ == '__main__':
    unittest.main()