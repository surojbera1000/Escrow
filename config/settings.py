"""
Configuration settings for the Telegram Escrow Bot.
Loads environment variables from .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ─── Telegram Bot Configuration ───────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "EscrowBot")
ADMIN_USER_IDS = [int(x) for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x.strip()]

# ─── MongoDB Configuration ────────────────────────────────────────────────────
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "escrow_bot")

# ─── Blockchain RPC Endpoints ─────────────────────────────────────────────────
BSC_RPC_URL = os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/")
TRON_RPC_URL = os.getenv("TRON_RPC_URL", "https://api.trongrid.io")
TRON_API_KEY = os.getenv("TRON_API_KEY", "")

# ─── USDT Contract Addresses ─────────────────────────────────────────────────
BSC_USDT_CONTRACT = os.getenv("BSC_USDT_CONTRACT", "0x55d398326f99059fF775485246999027B3197955")
TRON_USDT_CONTRACT = os.getenv("TRON_USDT_CONTRACT", "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t")

# ─── Escrow Wallet (Hot Wallet for receiving deposits) ────────────────────────
# BSC/BEP20
ESCROW_BSC_PRIVATE_KEY = os.getenv("ESCROW_BSC_PRIVATE_KEY", "")
ESCROW_BSC_ADDRESS = os.getenv("ESCROW_BSC_ADDRESS", "")

# TRON/TRC20
ESCROW_TRON_PRIVATE_KEY = os.getenv("ESCROW_TRON_PRIVATE_KEY", "")
ESCROW_TRON_ADDRESS = os.getenv("ESCROW_TRON_ADDRESS", "")

# ─── Trade Settings ───────────────────────────────────────────────────────────
DEPOSIT_ADDRESS_TIMEOUT_MINUTES = int(os.getenv("DEPOSIT_ADDRESS_TIMEOUT_MINUTES", "20"))
PAYMENT_CHECK_INTERVAL_SECONDS = int(os.getenv("PAYMENT_CHECK_INTERVAL_SECONDS", "60"))

# ─── Bot Fee (percentage) ─────────────────────────────────────────────────────
BOT_FEE_PERCENT = float(os.getenv("BOT_FEE_PERCENT", "1.0"))

# ─── Group Photo Path ─────────────────────────────────────────────────────────
GROUP_PHOTO_PATH = os.getenv("GROUP_PHOTO_PATH", "assets/escrow_group_photo.jpg")
