import turso_serverless
import os

from core.utils.logs import log_info

TURSO_URL = os.environ.get("TURSO_URL", "")
TURSO_TOKEN = os.environ.get("TURSO_TOKEN", "")

def get_connection():
    return turso_serverless.connect(
        url=TURSO_URL,
        auth_token=TURSO_TOKEN
    )
