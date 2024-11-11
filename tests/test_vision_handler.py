import unittest
import os
from pathlib import Path
from src.vision_handler import VisionHandler
import base64
import tempfile
import shutil

class TestVisionHandler(unittest.TestCase):
    def setUp(self):
        """테스트 환경을 설정합니다."""
        # 임시 디렉토리 생성
        self.test_dir = tempfile.mkdtemp()
        
        # 테스트용 이미지 파일 생성
        self.test_image_data = base64.b64decode("/9j/4AAQSkZJRgABAQEAYABgAAD//gA7Q1JFQVRPUjogZ2QtanBlZyB2MS4wICh1c2luZyBJSkcgSlBFRyB2NjIpLCBxdWFsaXR5ID0gOTAK/9sAQwADAgIDAgIDAwMDBAMDBAUIBQUEBAUKBwcGCAwKDAwLCgsLDQ4SEA0OEQ4LCxAWEBETFBUVFQwPFxgWFBgSFBUU/9sAQwEDBAQFBAUJBQUJFA0LDRQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQU/8AAEQgAIAAgAwEiAAIRAQMRAf/EAB8AAAEFAQEBAQEBAAAAAAAAAAABAgMEBQYHCAkKC//EALUQAAIBAwMCBAMFBQQEAAABfQECAwAEEQUSITFBBhNRYQcicRQygZGhCCNCscEVUtHwJDNicoIJChYXGBkaJSYnKCkqNDU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6g4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2drh4uPk5ebn6Onq8fLz9PX29/j5+v/EAB8BAAMBAQEBAQEBAQEAAAAAAAABAgMEBQYHCAkKC//EALURAAIBAgQEAwQHBQQEAAECdwABAgMRBAUhMQYSQVEHYXETIjKBCBRCkaGxwQkjM1LwFWJy0QoWJDThJfEXGBkaJicoKSo1Njc4OTpDREVGR0hJSlNUVVZXWFlaY2RlZmdoaWpzdHV2d3h5eoKDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uLj5OXm5+jp6vLz9PX29/j5+v/aAAwDAQACEQMRAD8A/VOiiigAooooAKKKKACiiigAooooAKKKKAP/2Q==")
        self.test_image_path = os.path.join(self.test_dir, "test_image.jpg")
        with open(self.test_image_path, "wb") as f:
            f.write(self.test_image_data)
            
        # 잘못된 형식의 파일 생성
        self.invalid_file_path = os.path.join(self.test_dir, "test.txt")
        with open(self.invalid_file_path, "w") as f:
            f.write("This is not an image")

    def tearDown(self):
        """테스트 환경을 정리합니다."""
        # 임시 디렉토리와 파일들 삭제
        shutil.rmtree(self.test_dir)

    def test_validate_image(self):
        """이미지 유효성 검사 테스트"""
        # 유효한 이미지 파일 테스트
        self.assertTrue(VisionHandler.validate_image(self.test_image_path))
        
        # 존재하지 않는 파일 테스트
        self.assertFalse(VisionHandler.validate_image("nonexistent.jpg"))
        
        # 잘못된 형식의 파일 테스트
        self.assertFalse(VisionHandler.validate_image(self.invalid_file_path))

    def test_get_media_type(self):
        """미디어 타입 반환 테스트"""
        # 지원되는 형식들 테스트
        self.assertEqual(VisionHandler.get_media_type("test.jpg"), "image/jpeg")
        self.assertEqual(VisionHandler.get_media_type("test.jpeg"), "image/jpeg")
        self.assertEqual(VisionHandler.get_media_type("test.png"), "image/png")
        self.assertEqual(VisionHandler.get_media_type("test.gif"), "image/gif")
        self.assertEqual(VisionHandler.get_media_type("test.webp"), "image/webp")
        
        # 지원되지 않는 형식 테스트
        self.assertIsNone(VisionHandler.get_media_type("test.txt"))
        self.assertIsNone(VisionHandler.get_media_type("test.doc"))

    def test_prepare_image_content(self):
        """이미지 콘텐츠 준비 테스트"""
        # 유효한 이미지 처리 테스트
        try:
            content = VisionHandler.prepare_image_content(self.test_image_path)
            self.assertEqual(content["type"], "image")
            self.assertEqual(content["source"]["type"], "base64")
            self.assertEqual(content["source"]["media_type"], "image/jpeg")
            self.assertIsInstance(content["source"]["data"], str)
            
            # base64 디코딩 테스트
            decoded_data = base64.b64decode(content["source"]["data"])
            self.assertEqual(decoded_data, self.test_image_data)
        except Exception as e:
            self.fail(f"유효한 이미지 처리 중 예외 발생: {str(e)}")
            
        # 잘못된 파일에 대한 예외 테스트
        with self.assertRaises(ValueError):
            VisionHandler.prepare_image_content(self.invalid_file_path)
            
        # 존재하지 않는 파일에 대한 예외 테스트
        with self.assertRaises(ValueError):
            VisionHandler.prepare_image_content("nonexistent.jpg")

    def test_large_image_handling(self):
        """대용량 이미지 처리 테스트"""
        # 큰 이미지 파일 생성 (1MB)
        large_image_path = os.path.join(self.test_dir, "large_image.jpg")
        with open(large_image_path, "wb") as f:
            f.write(os.urandom(1024 * 1024))
            
        try:
            content = VisionHandler.prepare_image_content(large_image_path)
            self.assertIsInstance(content["source"]["data"], str)
        except Exception as e:
            self.fail(f"대용량 이미지 처리 중 예외 발생: {str(e)}")

if __name__ == '__main__':
    unittest.main()