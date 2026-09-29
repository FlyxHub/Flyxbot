"""Runtime configuration for Flyxbot.

Every guild ID that used to be a magic number in the source lives here. Values are
read from the environment (optionally through a ``.env`` file).

Prefer a per-guild default over a configured ID: anything read from here is a single
snowflake shared by every guild the bot joins, so it can only ever be right in one of
them. Resolve from the guild or the invocation wherever Discord already gives an
answer, and gate commands on Discord's own permissions rather than on a role ID.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _id(name: str) -> int | None:
    raw = os.environ.get(name, "").strip()
    return int(raw) if raw else None


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable snapshot of the environment, built once at import time."""

    token: str | None
    command_prefix: str
    #: User who gets DM alerts when a message mentioning them is edited/deleted.
    owner_user_id: int
    #: Channel Flashback reads from the first and posts to the second; off unless both are set.
    flashback_channel_id: int | None
    flashback_target_channel_id: int | None
    #: IANA zone name for flashback's 9AM post and its day boundaries.
    flashback_timezone: str

    @classmethod
    def from_env(cls) -> Settings:
        raw_token = os.environ.get("DISCORD_TOKEN")
        return cls(
            # A .env created with CRLF line endings (e.g. on Windows, then run
            # through Docker's env_file on Linux) leaves a trailing \r on the
            # value that discord.py rejects as "Improper token has been passed".
            token=raw_token.strip() if raw_token else raw_token,
            command_prefix=os.environ.get("COMMAND_PREFIX", ">"),
            owner_user_id=_id("OWNER_USER_ID") or 307688449811415041,
            flashback_channel_id=_id("FLASHBACK_CHANNEL_ID"),
            flashback_target_channel_id=_id("FLASHBACK_TARGET_CHANNEL_ID"),
            flashback_timezone=os.environ.get("FLASHBACK_TIMEZONE", "").strip() or "UTC",
        )


settings = Settings.from_env()
