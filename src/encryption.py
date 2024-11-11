# src/encryption.py

from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 환경 변수 로드

# 환경 변수에서 암호화 키 가져오기
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

# Fernet 인스턴스 생성
fernet = Fernet(ENCRYPTION_KEY.encode())

def encrypt_data(data: str) -> bytes:
    """문자열 데이터를 암호화합니다."""
    return fernet.encrypt(data.encode())

def decrypt_data(encrypted_data: bytes) -> str:
    """암호화된 바이트 데이터를 복호화하여 문자열로 반환합니다."""
    return fernet.decrypt(encrypted_data).decode()