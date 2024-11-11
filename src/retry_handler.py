import asyncio
import time
from typing import Callable, Any, Dict, Type
from functools import wraps
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RetryHandler:
    """API 호출 재시도 및 에러 처리를 담당하는 클래스"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """
        RetryHandler 인스턴스를 초기화합니다.

        Args:
            max_retries (int): 최대 재시도 횟수
            base_delay (float): 기본 대기 시간(초)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.error_handlers: Dict[Type[Exception], Callable] = {}

    def register_error_handler(self, error_type: Type[Exception], handler: Callable) -> None:
        """
        특정 에러 타입에 대한 핸들러를 등록합니다.

        Args:
            error_type (Type[Exception]): 처리할 예외 타입
            handler (Callable): 에러 처리 함수
        """
        self.error_handlers[error_type] = handler

    def calculate_delay(self, attempt: int, jitter: bool = True) -> float:
        """
        재시도 대기 시간을 계산합니다.

        Args:
            attempt (int): 현재 시도 횟수
            jitter (bool): 무작위성 추가 여부

        Returns:
            float: 계산된 대기 시간(초)
        """
        delay = self.base_delay * (2 ** attempt)  # 지수 백오프
        if jitter:
            delay *= (0.5 + 0.5 * time.time() % 1)  # 무작위성 추가
        return delay

    @staticmethod
    def is_retryable_error(error: Exception) -> bool:
        """
        재시도 가능한 에러인지 확인합니다.

        Args:
            error (Exception): 확인할 예외 객체

        Returns:
            bool: 재시도 가능하면 True, 아니면 False
        """
        from anthropic import APIError
        if isinstance(error, APIError):
            return error.status_code in [429, 500, 503]  # Rate limit, 서버 에러
        return False

    async def async_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        비동기 함수에 대한 재시도 로직을 구현합니다.

        Args:
            func (Callable): 실행할 비동기 함수
            *args: 함수에 전달할 위치 인자
            **kwargs: 함수에 전달할 키워드 인자

        Returns:
            Any: 함수의 실행 결과

        Raises:
            Exception: 모든 재시도가 실패했을 때 마지막 발생한 예외
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {str(e)}")
                
                handler = self.error_handlers.get(type(e))
                if handler:
                    handler(e, attempt)

                if attempt == self.max_retries - 1 or not self.is_retryable_error(e):
                    logger.error(f"All retry attempts failed: {str(e)}")
                    raise last_error

                delay = self.calculate_delay(attempt)
                logger.info(f"Waiting {delay:.2f} seconds before next attempt...")
                await asyncio.sleep(delay)
                
        raise last_error

    def retry(self, func: Callable) -> Callable:
        """
        동기 함수에 대한 재시도 데코레이터를 제공합니다.

        Args:
            func (Callable): 데코레이트할 함수

        Returns:
            Callable: 재시도 로직이 추가된 래퍼 함수
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(self.max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {str(e)}")
                    
                    handler = self.error_handlers.get(type(e))
                    if handler:
                        handler(e, attempt)
                        
                    if attempt == self.max_retries - 1 or not self.is_retryable_error(e):
                        logger.error(f"All retry attempts failed: {str(e)}")
                        raise last_error
                        
                    delay = self.calculate_delay(attempt)
                    logger.info(f"Waiting {delay:.2f} seconds before next attempt...")
                    time.sleep(delay)
                    
            raise last_error
            
        return wrapper