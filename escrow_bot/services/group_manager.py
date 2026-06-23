"""Escrow group creation via a Telethon **user** session.

Why a user session?
-------------------
The Telegram **Bot API cannot create groups** - bots can only be *added* to
existing chats. To replicate the PAGAL flow where pressing /escrow spins up a
brand-new private group, we drive a regular user account through MTProto
(Telethon). That user account:

1. creates a new private supergroup,
2. invites the bot and promotes it to administrator,
3. exports an invite link,

then hands the chat id + invite link back to the bot, which manages the deal
from there on using the normal Bot API.

Generate the ``USERBOT_SESSION`` string once with ``scripts/generate_session.py``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class CreatedGroup:
    chat_id: int
    invite_link: str
    title: str


class GroupManager:
    """Wraps a Telethon user client used solely for group provisioning."""

    def __init__(self) -> None:
        self._client = None  # telethon.TelegramClient, lazily created
        self._available = bool(
            settings.api_id and settings.api_hash and settings.userbot_session
        )

    @property
    def available(self) -> bool:
        return self._available

    async def start(self) -> None:
        if not self._available:
            logger.warning(
                "GroupManager disabled: API_ID/API_HASH/USERBOT_SESSION not configured. "
                "/escrow will fall back to manual group setup instructions."
            )
            return
        from telethon import TelegramClient
        from telethon.sessions import StringSession

        self._client = TelegramClient(
            StringSession(settings.userbot_session), settings.api_id, settings.api_hash
        )
        await self._client.connect()
        if not await self._client.is_user_authorized():
            logger.error("Userbot session is not authorized. Regenerate USERBOT_SESSION.")
            self._available = False

    async def stop(self) -> None:
        if self._client is not None:
            await self._client.disconnect()

    async def create_escrow_group(self, deal_ref: str) -> Optional[CreatedGroup]:
        """Create a private supergroup, add+promote the bot, return invite link."""
        if not self._available or self._client is None:
            return None

        from telethon.tl.functions.channels import (
            CreateChannelRequest,
            EditAdminRequest,
            InviteToChannelRequest,
        )
        from telethon.tl.functions.messages import ExportChatInviteRequest
        from telethon.tl.types import ChatAdminRights

        title = f"Escrow Deal {deal_ref}"

        # 1) Create a megagroup (private supergroup)
        result = await self._client(
            CreateChannelRequest(
                title=title,
                about="Private escrow group. Share the invite with the buyer and seller.",
                megagroup=True,
            )
        )
        channel = result.chats[0]

        # 2) Invite the bot
        bot_username = settings.bot_username.lstrip("@")
        try:
            await self._client(InviteToChannelRequest(channel=channel, users=[bot_username]))
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to add bot to group: %s", exc)

        # 3) Promote the bot to administrator
        admin_rights = ChatAdminRights(
            change_info=True,
            post_messages=True,
            edit_messages=True,
            delete_messages=True,
            ban_users=True,
            invite_users=True,
            pin_messages=True,
            add_admins=False,
            manage_call=True,
        )
        try:
            await self._client(
                EditAdminRequest(
                    channel=channel,
                    user_id=bot_username,
                    admin_rights=admin_rights,
                    rank="Escrow Bot",
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to promote bot to admin: %s", exc)

        # 4) Export an invite link
        invite = await self._client(ExportChatInviteRequest(peer=channel))
        invite_link = getattr(invite, "link", "")

        # Bot API chat ids for supergroups are -100<channel_id>
        chat_id = int(f"-100{channel.id}")

        return CreatedGroup(chat_id=chat_id, invite_link=invite_link, title=title)


group_manager = GroupManager()
