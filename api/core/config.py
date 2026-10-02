import os
from pathlib import Path
from dotenv import load_dotenv

api_env = Path(__file__).resolve().parent.parent / '.env'
root_env = Path(__file__).resolve().parent.parent.parent / '.env'
if api_env.exists():
    load_dotenv(dotenv_path=api_env)
if root_env.exists():
    load_dotenv(dotenv_path=root_env)
load_dotenv()


def require_env(key: str) -> str:
    value = os.getenv(key)
    if not value or not value.strip():
        raise RuntimeError(f"Required environment variable is not configured: '{key}'.")
    return value.strip()


def get_env(key: str, default: str = "") -> str:
    value = os.getenv(key)
    if value is None or not value.strip():
        return default
    return value.strip()
