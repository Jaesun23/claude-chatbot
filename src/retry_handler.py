import asyncio
import time
from typing import Callable, Any, Dict, Type, Optional, Union
from functools import wraps
import logging
import random
from anthropic import APIError

logger = logging.getLogger(__name__)

class RetryHandler:
    """API 호출 재시도 및 에러 처리를 담당하는 클래스"""
    
    def __init__(self, 
                 max_retries: int = 3, 
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0):
        """
        RetryHandler 인스턴스를 초기화합니다.

        Args:
            max_retries (int): 최대 재시도 횟수
            base_delay (float): 기본 대기 시간(초)
            max_delay (float): 최대 대기 시간(초)
            exponential_base (float): 지수 백오프의 기본값
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.error_handlers: Dict[Type[Exception], Callable] = {}
        
        # 기본 에러 핸들러 등록
        self._register_default_handlers()
        
        logger.info(f"RetryHandler initialized with max_retries={max_retries}, "
                   f"base_delay={base_delay}, max_delay={max_delay}")

    def _register_default_handlers(self):
        """기본 에러 핸들러들을 등록합니다."""
        def handle_api_rate_limit(error: APIError, attempt: int):
            """API 속도 제한 에러 처리"""
            logger.warning(f"Rate limit exceeded (attempt {attempt + 1}/{self.max_retries}). "
                         f"Waiting before retry...")

        def handle_api_server_error(error: APIError, attempt: int):
            """API 서버 에러 처리"""
            logger.error(f"Server error occurred (attempt {attempt + 1}/{self.max_retries}): "
                        f"{str(error)}")

        def handle_network_error(error: Exception, attempt: int):
            """네트워크 관련 에러 처리"""
            logger.warning(f"Network error occurred (attempt {attempt + 1}/{self.max_retries}): "
                         f"{str(error)}")

        self.register_error_handler(APIError, handle_api_rate_limit, 
                                  error_codes=[429])
        self.register_error_handler(APIError, handle_api_server_error, 
                                  error_codes=[500, 502, 503, 504])
        self.register_error_handler((ConnectionError, TimeoutError), 
                                  handle_network_error)

    def register_error_handler(self, 
                             error_type: Union[Type[Exception], tuple],
                             handler: Callable,
                             error_codes: Optional[list] = None) -> None:
        """
        특정 에러 타입에 대한 핸들러를 등록합니다.

        Args:
            error_type: 처리할 예외 타입 또는 타입들의 튜플
            handler: 에러 처리 함수
            error_codes: APIError의 경우 처리할 에러 코드 목록
        """
        if error_codes:
            original_handler = handler
            def code_specific_handler(error: APIError, attempt: int):
                if hasattr(error, 'status_code') and error.status_code in error_codes:
                    return original_handler(error, attempt)
            handler = code_specific_handler
            
        self.error_handlers[error_type] = handler
        logger.debug(f"Registered error handler for {error_type}")

    def calculate_delay(self, 
                       attempt: int, 
                       error: Optional[Exception] = None,
                       jitter: bool = True) -> float:
        """
        재시도 대기 시간을 계산합니다.

        Args:
            attempt: 현재 시도 횟수
            error: 발생한 예외 객체
            jitter: 무작위성 추가 여부

        Returns:
            float: 계산된 대기 시간(초)
        """
        # 기본 지수 백오프 계산
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        # API 속도 제한의 경우 서버가 제공하는 대기 시간 사용
        if isinstance(error, APIError) and error.status_code == 429:
            retry_after = getattr(error, 'retry_after', None)
            if retry_after:
                delay = float(retry_after)

        # 지터 추가
        if jitter:
            delay *= (0.5 + random.random())
            
        return delay

    def is_retryable_error(self, error: Exception) -> bool:
        """
        재시도 가능한 에러인지 확인합니다.

        Args:
            error: 확인할 예외 객체

        Returns:
            bool: 재시도 가능하면 True, 아니면 False
        """
        # API 에러 처리
        if isinstance(error, APIError):
            return error.status_code in [429, 500, 502, 503, 504]
            
        # 네트워크 관련 에러 처리
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True
            
        # 에러 핸들러가 등록된 에러 타입 처리
        for error_type in self.error_handlers:
            if isinstance(error, error_type):
                return True
                
        return False

    async def async_retry(self, 
                         func: Callable, 
                         *args, 
                         custom_max_retries: Optional[int] = None,
                         **kwargs) -> Any:
        """
        비동기 함수에 대한 재시도 로직을 구현합니다.

        Args:
            func: 실행할 비동기 함수
            *args: 함수에 전달할 위치 인자
            custom_max_retries: 이 호출에 대한 커스텀 최대 재시도 횟수
            **kwargs: 함수에 전달할 키워드 인자

        Returns:
            Any: 함수의 실행 결과

        Raises:
            Exception: 모든 재시도가 실패했을 때 마지막으로 발생한 예외
        """
        max_retries = custom_max_retries or self.max_retries
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
                
            except Exception as e:
                last_error = e
                
                # 에러 핸들러 실행
                for error_type, handler in self.error_handlers.items():
                    if isinstance(e, error_type):
                        handler(e, attempt)
                        break
                
                # 재시도 불가능한 에러면 즉시 종료
                if not self.is_retryable_error(e):
                    logger.error(f"Non-retryable error occurred: {str(e)}")
                    raise

                if attempt == max_retries - 1:
                    logger.error(f"All retry attempts failed: {str(e)}")
                    raise last_error

                # 대기 시간 계산 및 대기
                delay = self.calculate_delay(attempt, error=e)
                logger.info(f"Waiting {delay:.2f} seconds before retry...")
                await asyncio.sleep(delay)
        
        raise last_error

    def retry(self, 
              custom_max_retries: Optional[int] = None,
              custom_base_delay: Optional[float] = None) -> Callable:
        """
        동기 함수에 대한 재시도 데코레이터를 제공합니다.

        Args:
            custom_max_retries: 커스텀 최대 재시도 횟수
            custom_base_delay: 커스텀 기본 대기 시간

        Returns:
            Callable: 재시도 로직이 추가된 래퍼 함수
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                max_retries = custom_max_retries or self.max_retries
                base_delay = custom_base_delay or self.base_delay
                last_error = None
                
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                        
                    except Exception as e:
                        last_error = e
                        
                        # 에러 핸들러 실행
                        for error_type, handler in self.error_handlers.items():
                            if isinstance(e, error_type):
                                handler(e, attempt)
                                break
                        
                        # 재시도 불가능한 에러면 즉시 종료
                        if not self.is_retryable_error(e):
                            logger.error(f"Non-retryable error occurred: {str(e)}")
                            raise

                        if attempt == max_retries - 1:
                            logger.error(f"All retry attempts failed: {str(e)}")
                            raise last_error

                        # 대기 시간 계산 및 대기
                        delay = self.calculate_delay(
                            attempt, 
                            error=e, 
                            jitter=True
                        )
                        logger.info(f"Waiting {delay:.2f} seconds before retry...")
                        time.sleep(delay)
                
                raise last_error
                
            return wrapper
        return decorator

    def __call__(self, func: Callable) -> Callable:
        """
        클래스를 직접 데코레이터로 사용할 수 있게 합니다.

        Args:
            func: 데코레이트할 함수

        Returns:
            Callable: 재시도 로직이 추가된 래퍼 함수
        """
        return self.retry()(func)