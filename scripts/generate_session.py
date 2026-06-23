"""One-time helper to generate a Telethon StringSession for the userbot.

Run this locally (interactive), enter the phone number + login code (and 2FA
password if enabled), then copy the printed session string into the
``USERBOT_SESSION`` variable in your ``.env`` file.

    python scripts/generate_session.py
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv()


def main() -> None:
    api_id = int(os.getenv("API_ID", "0"))
    api_hash = os.getenv("API_HASH", "")
    if not api_id or not api_hash:
        raise SystemExit("Set API_ID and API_HASH in your .env first.")

    with TelegramClient(StringSession(), api_id, api_hash) as client:
        print("\n=== Your USERBOT_SESSION string (keep it secret!) ===\n")
        print(client.session.save())
        print("\nPaste it into your .env as USERBOT_SESSION=...\n")


if __name__ == "__main__":
    main()
