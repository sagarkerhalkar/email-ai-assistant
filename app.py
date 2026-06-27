from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from email_ai_assistant.config import load_env_file

load_env_file()

from email_ai_assistant.server import run


if __name__ == "__main__":
    run()
