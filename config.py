import os
import logging

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")

admin_id_raw = os.getenv("ADMIN_ID")
ADMIN_ID = None
if admin_id_raw:
    try:
        ADMIN_ID = int(admin_id_raw)
    except Exception:
        logging.error("Environment variable ADMIN_ID is set but is not a valid integer: %r", admin_id_raw)

if not TOKEN:
    logging.error("Environment variable TOKEN is not set. The bot will not be able to start without it.")

if not MONGODB_URI:
    logging.error("Environment variable MONGODB_URI is not set. Database connection will fail without it.")

ADMIN_IDS = [ADMIN_ID] if ADMIN_ID else []
DATABASE_NAME = os.getenv("DATABASE_NAME", "find_team_system")
