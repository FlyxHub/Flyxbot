"""Runtime configuration for Flyxbot.

Every guild ID that used to be a magic number in the source lives here. Values
are read from the environment (optionally through a ``.env`` file) and fall back
to the IDs of the guild the bot was originally written for, so an existing
deployment keeps working once ``DISCORD_TOKEN`` is set.
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


def _snowflakes(name: str, default: tuple[int, ...]) -> tuple[int, ...]:
    raw = os.environ.get(name)
    if not raw or not raw.strip():
        return default
    try:
        return tuple(int(part) for part in raw.replace(",", " ").split())
    except ValueError as exc:
        raise RuntimeError(
            f"{name} must be a space/comma separated list of IDs, got {raw!r}"
        ) from exc


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable snapshot of the environment, built once at import time."""

    token: str | None
    command_prefix: str
    #: Restriction role. Having it *removes* the ability to post images.
    no_images_role_id: int
    #: Role that gates the image, roulette and slowmode commands.
    moderator_role_id: int
    #: Role whose ``send_messages`` is toggled by ``ld enable`` / ``ld disable``.
    lockdown_role_id: int
    #: User who gets DM alerts when a message mentioning them is edited/deleted.
    owner_user_id: int
    #: Users who receive the restriction role as soon as they join.
    join_blacklist: tuple[int, ...]

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            token=os.environ.get("DISCORD_TOKEN") or os.environ.get("TOKEN"),
            command_prefix=os.environ.get("COMMAND_PREFIX", ">"),
            no_images_role_id=_snowflake("NO_IMAGES_ROLE_ID", 1041203946817081365),
            moderator_role_id=_snowflake("MODERATOR_ROLE_ID", 1042085580034539580),
            lockdown_role_id=_snowflake("LOCKDOWN_ROLE_ID", 1036799478608429116),
            owner_user_id=_snowflake("OWNER_USER_ID", 307688449811415041),
            join_blacklist=_snowflakes("JOIN_BLACKLIST", (787885272594513950, 514143503471738910)),
        )


settings = Settings.from_env()
