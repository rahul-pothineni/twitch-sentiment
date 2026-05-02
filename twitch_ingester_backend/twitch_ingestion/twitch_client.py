"""
Filename: twitch_client.py
Author: Rahul Pothineni
Date: 2026-04-29
Description: Thin wrapper around the twitchAPI SDK that handles app + user
authentication and resolves a list of channel logins into TwitchUser objects.
"""

from twitchAPI.helper import first
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.type import AuthScope
from db.models import Session, Streamer

# Minimum scopes needed to read chat messages over EventSub.
SCOPES = [AuthScope.USER_READ_CHAT]


async def authenticate(app_id: str, app_secret: str):
    """Authenticate the app + the local dev user and return (twitch, me)."""
    twitch = await Twitch(app_id, app_secret)
    helper = UserAuthenticationStorageHelper(twitch, SCOPES)
    await helper.bind()
    me = await first(twitch.get_users())
    return twitch, me


async def resolve_target_channels(twitch: Twitch, channels: list[str], session: Session):
    """Resolve channel logins to TwitchUser objects, raising if any are missing."""
    targets = [user async for user in twitch.get_users(logins=channels)]
    found = {u.login.lower() for u in targets}
    for streamer_name in found:
        await Streamer.objects.aget_or_create(session = session, username = streamer_name)
    missing = [c for c in channels if c.lower() not in found]
    if missing:
        raise SystemExit(f"channels not found: {missing}")
    return targets