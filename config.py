import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

with open(env_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    TOKEN = lines[0].strip() if len(lines) > 0 else ""
    MONGODB_URI = lines[1].strip() if len(lines) > 1 else ""
    ADMIN_ID = int(lines[2].strip()) if len(lines) > 2 and lines[2].strip().isdigit() else None

ADMIN_IDS = [ADMIN_ID] if ADMIN_ID else []
DATABASE_NAME = "find_team_system"
