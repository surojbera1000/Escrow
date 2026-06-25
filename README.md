# Telegram Crypto Escrow Bot (PAGAL Clone)

A fully functional Telegram Escrow Bot for P2P cryptocurrency trades (USDT, BTC, LTC). Creates private escrow groups, manages buyer/seller roles, and handles fund release/refund commands with blockchain verification.

## Features

- **Escrow Group Creation** — Creates private groups with invite links
- **Deal Info Form** — Structured deal setup (Quantity, Rate, Conditions)
- **Role Assignment** — Seller/Buyer with wallet address verification
- **Token & Network Selection** — Interactive inline keyboards (USDT, BTC, LTC / BSC, TRON)
- **Deposit Address Generation** — Unique escrow wallet with timeout timer
- **Blockchain Payment Verification** — Real-time polling (BSC/BEP20, TRON/TRC20)
- **Fund Release/Refund** — Permission-controlled commands (seller only)
- **Dispute System** — Open disputes for admin resolution
- **Group Photo Automation** — Auto-changes group photo on trade start

## Project Structure

```
telegram-escrow-bot/
├── bot.py                    # Main entry point
├── config/
│   ├── __init__.py
│   └── settings.py           # Environment configuration
├── handlers/
│   ├── __init__.py
│   ├── start.py              # /start, /instructions, /balance, /save, /verify
│   ├── escrow.py             # /escrow - group creation
│   ├── deal.py               # /dd - deal info conversation
│   ├── roles.py              # /seller, /buyer - role assignment
│   ├── token.py              # /token - token/network selection
│   ├── trade.py              # Trade accept/reject, /deposit
│   └── release.py            # /release, /refund, /dispute
├── models/
│   ├── __init__.py
│   ├── database.py           # MongoDB connection singleton
│   ├── user.py               # User model
│   ├── trade.py              # Trade model with status management
│   └── escrow_group.py       # Escrow group model
├── services/
│   ├── __init__.py
│   ├── blockchain.py         # BSC & TRON payment verification
│   ├── payment_monitor.py    # Background payment polling job
│   └── group_photo.py        # Group photo automation
├── utils/
│   ├── __init__.py
│   ├── messages.py           # All message templates
│   └── keyboards.py          # Keyboard layouts
├── assets/
│   └── .gitkeep              # Place escrow_group_photo.jpg here
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Setup & Installation

### 1. Prerequisites

- Python 3.10+
- MongoDB (local or Atlas)
- Telegram Bot Token (from @BotFather)

### 2. Clone & Install

```bash
git clone <repo-url>
cd telegram-escrow-bot
python -m venv venv
source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required variables:
- `BOT_TOKEN` — Your Telegram bot token
- `MONGODB_URI` — MongoDB connection string
- `ESCROW_BSC_ADDRESS` — Your BSC escrow wallet address
- `ESCROW_TRON_ADDRESS` — Your TRON escrow wallet address

### 4. Run the Bot

```bash
python bot.py
```

## Bot Commands

| Command | Context | Description |
|---------|---------|-------------|
| `/start` | Private | Show main menu |
| `/instructions` | Private | Usage guide |
| `/escrow` | Private | Create escrow group |
| `/dd` | Group | Set deal info |
| `/seller [WALLET]` | Group | Declare as seller |
| `/buyer [WALLET]` | Group | Declare as buyer |
| `/token` | Group | Select token & network |
| `/deposit` | Group | Generate deposit address |
| `/release` | Group | Release funds (seller only) |
| `/refund` | Group | Refund funds (seller only) |
| `/dispute` | Group | Open dispute |
| `/balance` | Any | Check balance |
| `/save` | Any | Save trade state |
| `/verify` | Any | Verify identity |

## Trade Flow

1. User sends `/escrow` → Bot creates group with invite link
2. Both parties join → Use `/dd` to set deal terms
3. `/seller <wallet>` and `/buyer <wallet>` → Roles assigned
4. `/token` → Select crypto and network
5. Accept the escrow declaration
6. `/deposit` → Get escrow wallet address
7. Buyer sends funds → Bot detects payment automatically
8. `/release` → Seller releases funds to buyer

## Security Notes

- Only the assigned **Seller** can execute `/release` and `/refund`
- Wallet private keys should NEVER be shared or committed
- Use environment variables for all sensitive data
- The bot's hot wallet should hold minimal funds

## Tech Stack

- **python-telegram-bot v20+** — Async Telegram bot framework
- **pymongo** — MongoDB driver
- **web3.py** — BSC/BEP20 blockchain interaction
- **tronpy** — TRON/TRC20 blockchain interaction
- **httpx** — Async HTTP client for TRON API
