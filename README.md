# Telegram Crypto Escrow Bot

A Python clone of the **PAGAL Escrow Bot** workflow. It facilitates peer-to-peer
(P2P) crypto trades by creating private escrow groups, managing buyer/seller
roles, providing a deposit address, monitoring the blockchain for payment, and
handling fund release / refund commands.

> 💡 **Scope of this build:** Deposits are processed for **USDT on BSC [BEP20]
> only**, using a single fixed escrow receiving address. The other options
> (BTC, LTC, USDT-TRC20) still appear in the menus but reply that they are not
> available yet. This keeps the bot lightweight and dependency-free to deploy.

> ⚠️ **Important / legal note**: This software moves real cryptocurrency value
> on behalf of third parties. It is provided as a functional reference. Before
> using it with real funds you **must** add hardened key custody, dispute
> moderation, KYC/AML where required, and a real fund-sweeping/payout
> implementation. Operating an escrow service may be regulated in your
> jurisdiction.

---

## Features

| # | Feature | Command(s) | Status |
|---|---------|-----------|--------|
| 1 | Main menu reply keyboard | `/start` | ✅ |
| 2 | Create a private escrow group + invite link | `/escrow` | ✅ (via userbot) |
| 3 | Pinned welcome + Deal Info Form | `/dd` | ✅ |
| 4 | Seller / Buyer role declaration cards | `/seller`, `/buyer` | ✅ |
| 5 | Token + network inline selection, declaration card | `/token` | ✅ |
| 6 | Transaction info + deposit address (fixed BEP20 address) | `/deposit` | ✅ |
| 7 | USDT BEP20 payment verification (poll every 60s) | auto + `/balance` | ✅ |
| 8 | Fund release / refund (seller-only) | `/release`, `/refund` | ✅ |
| 9 | Auto group photo when a trade starts | automatic | ✅ |
|   | Dispute, save summary, verify checklist | `/dispute`, `/save`, `/verify` | ✅ |

---

## How `/escrow` creates a group (read this)

The **Telegram Bot API cannot create groups** — bots can only be *added* to
existing chats. The real PAGAL bot (and this clone) work around that by driving
a normal **user account** through MTProto with [Telethon](https://docs.telethon.dev/):

1. The user account creates a fresh private supergroup.
2. It invites the bot and promotes it to **administrator**.
3. It exports an invite link.
4. The bot then manages the whole deal through the regular Bot API.

If you don't configure a userbot session, `/escrow` degrades gracefully and
tells the user to create the group manually and add the bot as admin.

---

## Tech stack

- Python 3.10+
- [python-telegram-bot](https://docs.python-telegram-bot.org/) v21 (async)
- [Telethon](https://docs.telethon.dev/) (group creation via user session)
- MongoDB via [motor](https://motor.readthedocs.io/) (async) / pymongo
- `httpx` for BSC JSON-RPC `eth_call` balance checks (USDT BEP20)

> All dependencies are pure-Python / prebuilt wheels — no C or Rust toolchain is
> needed, so the build step won't fail on minimal deploy environments.

---

## Project layout

```
escrow_bot/
├── main.py             # entry point, wires handlers + lifecycle
├── __main__.py         # `python -m escrow_bot`
├── config.py           # env-driven settings
├── database.py         # async MongoDB access (trades, users)
├── models.py           # enums: TradeStatus, Token, Network
├── keyboards.py        # reply + inline keyboards
├── utils.py            # formatting / role helpers
├── handlers/
│   ├── start.py        # /start, /instructions
│   ├── escrow.py       # /escrow (group creation)
│   ├── deal.py         # /dd Deal Info Form (conversation)
│   ├── roles.py        # /seller, /buyer
│   ├── token.py        # /token + network + accept/reject
│   ├── deposit.py      # /deposit, /balance, payment polling
│   ├── settlement.py   # /release, /refund, /dispute
│   ├── group_photo.py  # auto group photo
│   └── misc.py         # /save, /verify
└── services/
    ├── group_manager.py # Telethon userbot
    └── blockchain.py    # USDT BEP20 balance check (JSON-RPC via httpx)
scripts/
└── generate_session.py  # one-time Telethon session string generator
```

---

## Setup

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in:

- `BOT_TOKEN` — from [@BotFather](https://t.me/BotFather)
- `BOT_USERNAME` — your bot's username (without `@`)
- `API_ID`, `API_HASH` — from <https://my.telegram.org>
- `MONGO_URI` / `MONGO_DB_NAME`
- `BEP20_DEPOSIT_ADDRESS` — your USDT BEP20 receiving address (a default is provided)

### 3. (Optional but recommended) Generate a userbot session

Needed so `/escrow` can create groups automatically:

```bash
python scripts/generate_session.py
```

Copy the printed string into `USERBOT_SESSION` in your `.env`.

### 4. Start MongoDB

Any MongoDB 4.4+ instance works (local Docker, Atlas, etc.).

### 5. Disable bot privacy mode (required)

The `/dd` Deal Info Form reads the trader's plain-text replies inside groups.
By default Telegram bots only see commands in groups, so you **must** disable
privacy mode: message [@BotFather](https://t.me/BotFather) → `/setprivacy` →
select your bot → **Disable**. (Then re-add the bot to existing groups.)

### 6. Run the bot

```bash
python -m escrow_bot
```

---

## Trade lifecycle (state machine)

```
open ──(/token accepted)──▶ accepted ──(/deposit)──▶ deposited
   └─(reject)─┘                                          │
                                              (payment detected)
                                                          ▼
                                                        paid
                                                  ┌───────┴────────┐
                                            (/release)        (/refund)
                                                ▼                 ▼
                                            released          refunded

any state ──(/dispute)──▶ disputed (funds frozen)
```

Trade documents are keyed by the escrow group's `chat_id` (see `database.py`
for the full schema).

---

## Security notes

- This build uses **one fixed deposit address** for all USDT BEP20 trades. To
  attribute a payment to a specific trade, the bot records the address balance
  when `/deposit` runs (a *baseline*) and reports the **increase** since then as
  that trade's incoming amount. Run one trade at a time for unambiguous matching,
  or move to per-trade generated addresses for high volume.
- `/release` and `/refund` are **logical** status changes. Wiring the actual
  on-chain payout (signing a transfer from the escrow wallet to the
  buyer/seller wallet) is left as a deliberate, security-sensitive next step.
- Always run the bot over a trusted network and keep the userbot session secret
  (`*.session` and `.env` are git-ignored).

---

## Notes on payment matching

`poll_payment_job` marks a trade as `paid` when the detected increase on the
deposit address reaches the expected amount. Set `deposit.amount_expected`
(e.g. derived from the Deal Info quantity × rate) to require an exact match; if
it's unset, any non-zero increase is treated as paid.
```
