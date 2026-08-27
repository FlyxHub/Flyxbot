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

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # python-dotenv is optional at runtime
    pass
else:
    load_dotenv()


def _snowflake(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a Discord ID (integer), got {raw!r}") from exc


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable snapshot of the environment, built once at import time."""

    token: str | None
    command_prefix: str
    #: User who gets DM alerts when a message mentioning them is edited/deleted.
    owner_user_id: int

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            token=os.environ.get("DISCORD_TOKEN") or os.environ.get("TOKEN"),
            command_prefix=os.environ.get("COMMAND_PREFIX", ">"),
            owner_user_id=_snowflake("OWNER_USER_ID", 307688449811415041),
        )


settings = Settings.from_env()
