import base64
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import logging
from PIL import Image
import io
import mimetypes
import hashlib
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class VisionHandler:
    """이미지 처리 및 비전 기능을 담당하는 클래스"""
    
    SUPPORTED_FORMATS = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    
    MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB
    MAX_DIMENSION = 4096  # 최대 이미지 차원
    CACHE_DIR = "image_cache"

    def __init__(self, cache_dir: Optional[str] = None):
        """
        VisionHandler 인스턴스를 초기화합니다.

        Args:
            cache_dir: 이미지 캐시 디렉토리 경로
        """
        self.cache_dir = cache_dir or self.CACHE_DIR
        self._ensure_cache_dir()
        self.cache_info: Dict[str, Dict] = {}
        logger.info("VisionHandler initialized")

    def _ensure_cache_dir(self) -> None:
        """캐시 디렉토리가 존재하는지 확인하고 없으면 생성합니다."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            logger.info(f"Created cache directory: {self.cache_dir}")

    def _calculate_file_hash(self, file_path: str) -> str:
        """
        파일의 SHA-256 해시를 계산합니다.

        Args:
            file_path: 해시를 계산할 파일 경로

        Returns:
            str: 파일의 해시값
        """
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def validate_image(self, image_path: str) -> Tuple[bool, Optional[str]]:
        """
        이미지 파일의 유효성을 검사합니다.

        Args:
            image_path: 검사할 이미지 파일 경로

        Returns:
            Tuple[bool, Optional[str]]: (유효성 여부, 오류 메시지)
        """
        try:
            path = Path(image_path)
            
            # 파일 존재 확인
            if not path.exists():
                return False, "File does not exist"
                
            # 확장자 확인
            if path.suffix.lower() not in self.SUPPORTED_FORMATS:
                return False, "Unsupported file format"
                
            # 파일 크기 확인
            if path.stat().st_size > self.MAX_IMAGE_SIZE:
                return False, "File size exceeds maximum limit"
                
            # 이미지 열기 시도
            with Image.open(image_path) as img:
                width, height = img.size
                if width > self.MAX_DIMENSION or height > self.MAX_DIMENSION:
                    return False, f"Image dimensions exceed {self.MAX_DIMENSION}x{self.MAX_DIMENSION}"
                    
            return True, None
            
        except Exception as e:
            logger.error(f"Image validation error: {str(e)}")
            return False, f"Invalid image file: {str(e)}"

    def get_media_type(self, image_path: str) -> Optional[str]:
        """
        이미지 파일의 미디어 타입을 반환합니다.

        Args:
            image_path: 이미지 파일 경로

        Returns:
            Optional[str]: 미디어 타입 문자열 또는 None
        """
        suffix = Path(image_path).suffix.lower()
        media_type = self.SUPPORTED_FORMATS.get(suffix)
        
        if not media_type:
            # mimetypes 라이브러리로 추가 확인
            media_type, _ = mimetypes.guess_type(image_path)
            
        return media_type if media_type in self.SUPPORTED_FORMATS.values() else None

    def optimize_image(self, image_path: str, quality: int = 85) -> Tuple[bytes, str]:
        """
        이미지를 최적화합니다.

        Args:
            image_path: 최적화할 이미지 파일 경로
            quality: JPEG 품질 설정 (1-100)

        Returns:
            Tuple[bytes, str]: (최적화된 이미지 데이터, 미디어 타입)
        """
        with Image.open(image_path) as img:
            # RGBA 이미지를 RGB로 변환
            if img.mode == 'RGBA':
                img = img.convert('RGB')
                
            # 이미지 크기 조정 (필요한 경우)
            if max(img.size) > self.MAX_DIMENSION:
                ratio = self.MAX_DIMENSION / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                
            # 이미지를 바이트로 변환
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            
            return buffer.getvalue(), 'image/jpeg'

    async def prepare_image_content(self, 
                                  image_path: str, 
                                  optimize: bool = True) -> Dict:
        """
        이미지를 API 요청에 맞는 형식으로 변환합니다.

        Args:
            image_path: 이미지 파일 경로
            optimize: 이미지 최적화 여부

        Returns:
            Dict: Claude API에 전송할 수 있는 형식의 이미지 데이터

        Raises:
            ValueError: 지원하지 않는 이미지 형식이거나 파일이 존재하지 않는 경우
            IOError: 파일 읽기 중 오류가 발생한 경우
        """
        # 이미지 유효성 검사
        is_valid, error_message = self.validate_image(image_path)
        if not is_valid:
            raise ValueError(f"Invalid image: {error_message}")
            
        try:
            # 캐시 확인
            file_hash = self._calculate_file_hash(image_path)
            cached_path = os.path.join(self.cache_dir, f"{file_hash}.cache")
            
            if os.path.exists(cached_path):
                with open(cached_path, 'rb') as f:
                    image_data = f.read()
                media_type = self.cache_info.get(file_hash, {}).get('media_type')
                
                logger.info(f"Using cached image: {image_path}")
                
            else:
                # 이미지 처리
                if optimize:
                    image_data, media_type = self.optimize_image(image_path)
                else:
                    with open(image_path, 'rb') as f:
                        image_data = f.read()
                    media_type = self.get_media_type(image_path)
                
                # 캐시 저장
                with open(cached_path, 'wb') as f:
                    f.write(image_data)
                    
                self.cache_info[file_hash] = {
                    'original_path': image_path,
                    'media_type': media_type,
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"Processed and cached image: {image_path}")

            # Base64 인코딩
            base64_image = base64.b64encode(image_data).decode('utf-8')

            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64_image
                }
            }
            
        except IOError as e:
            error_msg = f"이미지 파일 읽기 오류: {str(e)}"
            logger.error(error_msg)
            raise IOError(error_msg)
        except Exception as e:
            error_msg = f"이미지 처리 중 예상치 못한 오류 발생: {str(e)}"
            logger.error(error_msg)
            raise

    def cleanup_cache(self, max_age_days: int = 7) -> None:
        """
        오래된 캐시 파일들을 정리합니다.

        Args:
            max_age_days: 이 일수보다 오래된 캐시 파일들을 삭제
        """
        try:
            current_time = datetime.now()
            files_removed = 0
            
            for cache_file in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, cache_file)
                file_hash = cache_file.split('.')[0]
                
                # 캐시 정보 확인
                cache_info = self.cache_info.get(file_hash)
                if cache_info:
                    timestamp = datetime.fromisoformat(cache_info['timestamp'])
                    if (current_time - timestamp).days > max_age_days:
                        os.remove(file_path)
                        del self.cache_info[file_hash]
                        files_removed += 1
                else:
                    # 캐시 정보가 없는 파일은 삭제
                    os.remove(file_path)
                    files_removed += 1
                    
            logger.info(f"Cleaned up {files_removed} cached files")
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {str(e)}")

    def get_cache_stats(self) -> Dict:
        """
        캐시 통계를 반환합니다.

        Returns:
            Dict: 캐시 통계 정보
        """
        total_size = 0
        for file in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, file)
            total_size += os.path.getsize(file_path)
            
        return {
            'cache_count': len(self.cache_info),
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': self.cache_dir
        }