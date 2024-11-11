# src/response_formatter.py

import re
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter

def format_response(response: str) -> str:
    """
    Claude의 응답을 포맷팅합니다.
    - 코드 블록에 구문 강조를 적용합니다.
    - 마크다운 형식을 간단히 처리합니다.
    """
    # 코드 블록 처리
    def replace_code_block(match):
        language = match.group(1) or 'text'
        code = match.group(2)
        lexer = get_lexer_by_name(language, stripall=True)
        formatted_code = highlight(code, lexer, TerminalFormatter())
        return f"\n{formatted_code}\n"

    response = re.sub(r'```(\w+)?\n([\s\S]+?)\n```', replace_code_block, response)

    # 간단한 마크다운 처리
    response = re.sub(r'\*\*(.*?)\*\*', '\033[1m\\1\033[0m', response)  # 볼드 처리
    response = re.sub(r'\*(.*?)\*', '\033[3m\\1\033[0m', response)  # 이탤릭 처리

    return response