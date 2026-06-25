"""
Message templates and formatting utilities for the Escrow Bot.
"""

from datetime import datetime


def welcome_message(first_name: str) -> str:
    """Generate welcome message for /start."""
    return (
        f"👋 <b>Welcome, {first_name}!</b>\n\n"
        "🔐 <b>PAGAL Escrow Bot</b> — Your trusted P2P crypto escrow service.\n\n"
        "I facilitate safe Peer-to-Peer crypto trades (USDT, BTC, LTC) by creating "
        "private escrow groups, managing buyer/seller roles, and handling fund "
        "release/refund securely.\n\n"
        "📋 <b>How to get started:</b>\n"
        "1️⃣ Use /escrow to create a new escrow group\n"
        "2️⃣ Share the invite link with your trading partner\n"
        "3️⃣ Both parties set their roles (/seller & /buyer)\n"
        "4️⃣ Select token & network, then deposit funds\n"
        "5️⃣ Complete the trade with /release or /refund\n\n"
        "Use the menu buttons below to navigate. 👇"
    )


def instructions_message() -> str:
    """Generate instructions message."""
    return (
        "📖 <b>INSTRUCTIONS — How to Use the Escrow Bot</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Step 1:</b> Create an escrow group using /escrow\n"
        "<b>Step 2:</b> Share the group invite link with the other party\n"
        "<b>Step 3:</b> In the group, use /dd to set the deal info\n"
        "<b>Step 4:</b> Seller uses /seller [WALLET_ADDRESS]\n"
        "<b>Step 5:</b> Buyer uses /buyer [WALLET_ADDRESS]\n"
        "<b>Step 6:</b> Use /token to select cryptocurrency & network\n"
        "<b>Step 7:</b> Accept the deal terms\n"
        "<b>Step 8:</b> Buyer uses /deposit to get deposit address\n"
        "<b>Step 9:</b> Buyer sends funds to the deposit address\n"
        "<b>Step 10:</b> Once confirmed, seller uses /release to send funds to buyer\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ <b>Important Notes:</b>\n"
        "• Only the assigned SELLER can use /release and /refund\n"
        "• Always verify wallet addresses before confirming\n"
        "• Use /dispute if there's a disagreement\n"
        "• Never share your private keys\n\n"
        "🛡️ <b>Your funds are safe with us!</b>"
    )


def escrow_group_created_message(invite_link: str) -> str:
    """Message sent to user when escrow group is created."""
    return (
        "✅ <b>Escrow Group Created Successfully!</b>\n\n"
        f"🔗 <b>Invite Link:</b>\n{invite_link}\n\n"
        "📌 <b>Instructions:</b>\n"
        "1. Join the escrow group using the link above\n"
        "2. Share this invite link with the buyer/seller\n"
        "3. Once both parties are in the group, use /dd to set deal info\n\n"
        "⚠️ <i>This link is unique to your trade. Do not share publicly.</i>"
    )


def group_welcome_pin_message() -> str:
    """Pinned message in escrow group."""
    return (
        "👋 <b>Hey there traders!</b>\n\n"
        "Welcome to our escrow service. 🔐\n\n"
        "Please start with /dd command and fill the DealInfo Form.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 <b>Commands available in this group:</b>\n"
        "• /dd — Set deal information\n"
        "• /seller [WALLET] — Declare as seller\n"
        "• /buyer [WALLET] — Declare as buyer\n"
        "• /token — Select token & network\n"
        "• /deposit — Generate deposit address\n"
        "• /release — Release funds to buyer (seller only)\n"
        "• /refund — Refund funds to seller (seller only)\n"
        "• /dispute — Open a dispute\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def deal_info_message(quantity: str, rate: str, conditions: str) -> str:
    """Format deal info confirmation."""
    return (
        "📝 <b>DEAL INFORMATION</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 <b>Quantity:</b> {quantity}\n"
        f"📊 <b>Rate:</b> {rate}\n"
        f"📋 <b>Conditions:</b> {conditions if conditions else 'None'}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Deal info has been saved.\n"
        "Next: Seller and Buyer should declare their roles."
    )


def seller_declaration_card(username: str, user_id: int, wallet_address: str) -> str:
    """Seller role declaration card."""
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🏷️ <b>ESCROW-ROLE DECLARATION</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👤 <b>Role:</b> 🔴 SELLER\n"
        f"📛 <b>Username:</b> @{username}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        f"💳 <b>Wallet:</b> <code>{wallet_address}</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Seller role has been assigned."
    )


def buyer_declaration_card(username: str, user_id: int, wallet_address: str) -> str:
    """Buyer role declaration card."""
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🏷️ <b>ESCROW-ROLE DECLARATION</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👤 <b>Role:</b> 🟢 BUYER\n"
        f"📛 <b>Username:</b> @{username}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        f"💳 <b>Wallet:</b> <code>{wallet_address}</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Buyer role has been assigned."
    )


def escrow_declaration_card(buyer_username: str, buyer_id: int, token: str, network: str) -> str:
    """Escrow declaration card with accept/reject buttons."""
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📜 <b>ESCROW DECLARATION</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>Buyer:</b> @{buyer_username}\n"
        f"🆔 <b>Buyer ID:</b> <code>{buyer_id}</code>\n"
        f"💰 <b>Crypto:</b> {token}\n"
        f"🌐 <b>Network:</b> {network}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ <b>Do both parties agree to proceed?</b>"
    )


def transaction_info_message(seller: dict, buyer: dict, token: str, network: str, start_time: datetime) -> str:
    """Transaction information message after acceptance."""
    time_str = start_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 <b>TRANSACTION INFORMATION</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔴 <b>Seller:</b> @{seller['username']}\n"
        f"🟢 <b>Buyer:</b> @{buyer['username']}\n"
        f"💰 <b>Token:</b> {token}\n"
        f"🌐 <b>Network:</b> {network}\n"
        f"🕐 <b>Start Time:</b> {time_str}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ <b>IMPORTANT:</b>\n"
        "Make sure to finalise and agree each-others terms before depositing. "
        "Please use /deposit command to generate a deposit address for your trade.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def deposit_address_message(address: str, token: str, network: str, timeout_minutes: float) -> str:
    """Deposit address message with timer."""
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💳 <b>DEPOSIT ADDRESS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 <b>Token:</b> {token}\n"
        f"🌐 <b>Network:</b> {network}\n\n"
        f"📬 <b>Send funds to:</b>\n"
        f"<code>{address}</code>\n\n"
        f"⏱️ <b>Address Reset Timer:</b> {timeout_minutes:.2f} minutes\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💵 <b>Amount Received:</b> 0.00000 [0.00$]\n\n"
        "⚠️ <i>Send ONLY the exact agreed amount to this address.</i>\n"
        "⚠️ <i>Send ONLY on the correct network. Wrong network = lost funds.</i>"
    )


def payment_received_message(amount: float, token: str) -> str:
    """Payment received confirmation."""
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ <b>PAYMENT RECEIVED</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💵 <b>Amount Received:</b> {amount:.5f} {token}\n\n"
        "The funds are now held in escrow.\n"
        "Seller can use /release to send funds to buyer.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def funds_released_message(buyer_username: str) -> str:
    """Funds released confirmation."""
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ <b>FUNDS RELEASED</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💸 Funds Released To Buyer (@{buyer_username}).\n\n"
        "🎉 Trade completed successfully!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def funds_refunded_message(seller_username: str) -> str:
    """Funds refunded confirmation."""
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔄 <b>FUNDS REFUNDED</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💸 Funds Refunded To Seller (@{seller_username}).\n\n"
        "Trade has been cancelled and refunded.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def dispute_opened_message(username: str) -> str:
    """Dispute opened message."""
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ <b>DISPUTE OPENED</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🚨 A dispute has been opened by @{username}.\n\n"
        "An admin will review this trade and make a decision.\n"
        "Please provide any evidence or information to support your case.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def balance_message(user_id: int, username: str) -> str:
    """Balance inquiry message."""
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💰 <b>BALANCE INFORMATION</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>User:</b> @{username}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n\n"
        "💵 <b>Available Balance:</b> 0.00 USDT\n"
        "🔒 <b>In Escrow:</b> 0.00 USDT\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Balance reflects only funds held by the bot.</i>"
    )
