# Claude Chatbot

이 프로젝트는 Anthropic의 Claude API를 사용하여 구현한 대화형 챗봇입니다.

## 기능

- 다중 세션 관리
- 마크다운 형식의 응답 처리
- 코드 블록 하이라이팅
- 토큰 사용량 모니터링
- max_tokens 및 temperature 설정

## 설치

1. 이 저장소를 클론합니다:
git clone https://github.com/yourusername/claude-chatbot.git

2. 프로젝트 디렉토리로 이동합니다:
cd claude-chatbot

3. 필요한 패키지를 설치합니다:
pip install -r requirements.txt

4. `config/config.yaml` 파일을 생성하고 Anthropic API 키를 추가합니다:
```yaml
api_key: "your_api_key_here"


## 환경 설정

1. `.env.example` 파일을 `.env`로 복사합니다:
cp .env.example .env

2. `.env` 파일을 열고 `ANTHROPIC_API_KEY`와 `ENCRYPTION_KEY`를 설정합니다:
- `ANTHROPIC_API_KEY`: Anthropic API 키를 암호화한 값
- `ENCRYPTION_KEY`: 대화 내용 암호화에 사용할 키

3. Python 버전 설정:
이 프로젝트는 Python 3.12.4를 사용합니다. pyenv를 사용하여 Python 버전을 설정하세요:
pyenv install 3.12.4
pyenv local 3.9.5


## 보안

- API 키는 암호화되어 환경변수로 저장됩니다.
- 대화 내용은 저장 시 암호화되며, 로드 시 복호화됩니다.
- 암호화 키를 안전하게 관리해주세요.


## 사용법
프로그램을 실행하려면:
python main.py

## 개발
src/ 디렉토리에는 주요 소스 코드가 있습니다.
tests/ 디렉토리에는 단위 테스트가 있습니다.
새로운 기능을 추가할 때는 해당하는 테스트도 작성해주세요.

## 기여
버그를 발견하거나 새로운 기능을 제안하고 싶다면 이슈를 열어주세요.
풀 리퀘스트도 환영합니다!

## 라이선스
이 프로젝트는 MIT 라이선스 하에 있습니다.