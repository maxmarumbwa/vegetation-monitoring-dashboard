import os
from pathlib import Path
import ee
from google.oauth2 import service_account

BASE_DIR = Path(__file__).resolve().parent.parent

_ee_initialized = False


def initialize_earth_engine():
    global _ee_initialized

    # Prevent duplicate initialization
    if _ee_initialized:
        return

    try:
        key_path = os.environ.get("EE_KEY_PATH")

        if key_path:
            credentials = service_account.Credentials.from_service_account_file(
                key_path,
                scopes=["https://www.googleapis.com/auth/earthengine"],
            )

            print("🔐 Using Render secret file for Earth Engine authentication")

        else:
            local_key = BASE_DIR / "gee_key" / "ee-key.json"

            credentials = service_account.Credentials.from_service_account_file(
                local_key,
                scopes=["https://www.googleapis.com/auth/earthengine"],
            )

            print(f"💻 Using local Earth Engine key: {local_key}")

        ee.Initialize(credentials)

        _ee_initialized = True

        print("✅ Earth Engine initialized successfully")

    except Exception as e:
        print(f"❌ Earth Engine initialization failed: {e}")
