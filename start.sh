#!/usr/bin/env zsh

set -e  # 오류 발생 시 즉시 종료
set -x  # 실행되는 명령어 출력

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

PYTHON_VERSION="3.12.4"
PROJECT_ROOT="/Users/jaesun/Projects/claude-chatbot"
VENV_DIR="$PROJECT_ROOT/venv"
SRC_DIR="$PROJECT_ROOT/src"

log "Changing directory to project root: $PROJECT_ROOT"
cd "$PROJECT_ROOT"
log "Current directory: $(pwd)" 

# pyenv 초기화
if command -v pyenv 1>/dev/null 2>&1; then
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
else
    log "pyenv is not installed or not found in PATH"
    exit 1
fi

# pyenv를 사용하여 설정한 Python 버전이 있는지 확인
if ! pyenv versions --bare | grep -q "^${PYTHON_VERSION}\$"; then
    log "Python ${PYTHON_VERSION} not found. Installing..."
    pyenv install "$PYTHON_VERSION" || { log "Failed to install Python ${PYTHON_VERSION}"; exit 1; }
fi

# pyenv shell 설정
log "Setting pyenv version to ${PYTHON_VERSION}"
pyenv shell "$PYTHON_VERSION"

# virtualenv 설치 확인 및 가상환경 생성
if ! pip list | grep virtualenv > /dev/null; then
    log "virtualenv not found. Installing..."
    pip install virtualenv || { log "Failed to install virtualenv"; exit 1; }
fi

if [ ! -d "$VENV_DIR" ]; then
    log "Virtual environment not found. Creating one using virtualenv..."
    python -m virtualenv "$VENV_DIR" || { log "Failed to create virtual environment"; exit 1; }
fi

log "Activating virtual environment..."
source "$VENV_DIR/bin/activate" || { log "Failed to activate virtual environment"; exit 1; }

if [ -z "$VIRTUAL_ENV" ]; then
    log "Virtual environment activation failed. VIRTUAL_ENV is not set."; exit 1
fi

log "VIRTUAL_ENV: $VIRTUAL_ENV"

PYTHON_VERSION_ACTUAL=$("$VENV_DIR/bin/python" --version 2>&1)
log "Using $PYTHON_VERSION_ACTUAL"

log "Upgrading pip..."
"$VENV_DIR/bin/python" -m pip install --upgrade pip || { log "Failed to upgrade pip"; exit 1; }

log "Installing required packages..."
"$VENV_DIR/bin/pip" install -r requirements.txt || { log "Failed to install required packages"; exit 1; }

# PYTHONPATH 설정
export PYTHONPATH="$SRC_DIR"
log "PYTHONPATH set to $PYTHONPATH"

log "Running main Python script..."
PYTHONPATH="$SRC_DIR" "$VENV_DIR/bin/python" "$PROJECT_ROOT/main.py" || { log "Failed to run main.py"; exit 1; }

log "Script execution completed successfully."

set +x