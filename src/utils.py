# src/utils.py

import uuid
import os
import base64
from typing import List, Dict
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

def decrypt_api_key():
    encryption_key = os.getenv('ENCRYPTION_KEY')
    encrypted_api_key = os.getenv('ENCRYPTED_ANTHROPIC_API_KEY')
    
    if not encryption_key or not encrypted_api_key:
        raise ValueError("ENCRYPTION_KEY 또는 ENCRYPTED_ANTHROPIC_API_KEY가 설정되지 않았습니다.")
    
    f = Fernet(encryption_key.encode())
    decrypted_api_key = f.decrypt(base64.b64decode(encrypted_api_key))
    return decrypted_api_key.decode()

def count_tokens(messages: List[Dict]) -> int:
    """
    메시지 리스트의 총 토큰 수를 대략적으로 계산합니다.
    정확한 계산을 위해서는 실제 토크나이저를 사용해야 합니다.
    """
    return sum(len(msg['content'].split()) for msg in messages)

def generate_message_id() -> str:
    """
    고유한 메시지 ID를 생성합니다.
    """
    return str(uuid.uuid4())

def truncate_conversation(messages: List[Dict], max_tokens: int) -> List[Dict]:
    """
    대화 기록을 최대 토큰 수에 맞게 자릅니다.
    """
    truncated = []
    current_tokens = 0
    for message in reversed(messages):
        message_tokens = len(message['content'].split())
        if current_tokens + message_tokens > max_tokens:
            break
        truncated.insert(0, message)
        current_tokens += message_tokens
    return truncated