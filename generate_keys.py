from cryptography.fernet import Fernet
import base64
import os

def generate_env_file():
    """암호화 키를 생성하고 API 키를 암호화하여 .env 파일을 생성합니다."""
    
    # Fernet 키 생성
    encryption_key = Fernet.generate_key()
    
    # API 키 입력 받기
    api_key = input("Anthropic API 키를 입력하세요: ").strip()
    
    # API 키 암호화
    f = Fernet(encryption_key)
    encrypted_api_key = base64.b64encode(f.encrypt(api_key.encode())).decode()
    
    # .env 파일 생성
    env_content = f"""# Encryption key for securing sensitive data
ENCRYPTION_KEY={encryption_key.decode()}

# Encrypted Anthropic API key
ENCRYPTED_ANTHROPIC_API_KEY={encrypted_api_key}
"""
    
    # .env 파일 쓰기
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("\n.env 파일이 생성되었습니다.")
    print("주의: .env 파일을 안전하게 보관하고 절대로 공개하지 마세요!")

if __name__ == "__main__":
    try:
        generate_env_file()
    except Exception as e:
        print(f"오류 발생: {str(e)}")